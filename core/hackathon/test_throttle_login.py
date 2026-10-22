from unittest import mock

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from .models import SolicitacaoPerfil, User
from .models.user import tipoUser


class ThrottleLoginRegistroTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def tearDown(self):
        cache.clear()

    def test_login_limita_tentativas(self):
        taxas = {**SimpleRateThrottle.THROTTLE_RATES, "login": "2/min"}
        with mock.patch.object(SimpleRateThrottle, "THROTTLE_RATES", taxas):
            codigos = [
                self.client.post("/api/token/", {"username": "x", "password": "y"}).status_code
                for _ in range(3)
            ]
        self.assertEqual(codigos[:2], [401, 401])
        self.assertEqual(codigos[2], 429)

    def test_registro_limita_criacao_de_contas(self):
        taxas = {**SimpleRateThrottle.THROTTLE_RATES, "registro": "2/hour"}
        with mock.patch.object(SimpleRateThrottle, "THROTTLE_RATES", taxas):
            codigos = [
                self.client.post(
                    "/api/auth/registro/",
                    {"email": f"u{i}@ex.com", "password": "Senha-Forte-123"},
                    format="json",
                ).status_code
                for i in range(3)
            ]
        self.assertEqual(codigos[:2], [201, 201])
        self.assertEqual(codigos[2], 429)


class AprovacaoAtomicaTests(TestCase):
    def test_falha_ao_salvar_perfil_desfaz_a_decisao(self):
        usuario = User.objects.create_user(username="a", email="a@ex.com", password="Senha-Forte-123")
        admin = User.objects.create_user(
            username="adm", email="adm@ex.com", password="Senha-Forte-123", tipoUser=tipoUser.admin
        )
        sol = SolicitacaoPerfil.objects.create(usuario=usuario, perfil_solicitado=tipoUser.avaliador)
        with mock.patch.object(User, "save", side_effect=RuntimeError("falha")):
            with self.assertRaises(RuntimeError):
                sol.aprovar(admin)
        sol.refresh_from_db()
        self.assertEqual(sol.status, SolicitacaoPerfil.Status.PENDENTE)
