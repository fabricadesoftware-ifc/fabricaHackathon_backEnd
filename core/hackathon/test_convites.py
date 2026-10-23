from django.test import override_settings

from .models import ConviteEquipe, ParticipanteEquipe
from .test_regras_negocio import Base


@override_settings(FRONTEND_URL="https://front.test")
class LinkConviteTest(Base):
    def setUp(self):
        super().setUp()
        self.equipe = self.criar_equipe("Alfa", self.u1)
        self.url = f"/api/inscricoes/{self.equipe.id}/"

    def gerar(self):
        return self.as_user(self.u1).post(self.url + "link-convite/").json()["link_convite"]

    def test_gerar_trocar_e_revogar_link(self):
        link = self.gerar()
        self.assertTrue(link["url"].startswith("https://front.test/convite/"))
        novo = self.gerar()
        self.assertNotEqual(link["token"], novo["token"])
        self.assertEqual(ConviteEquipe.objects.filter(ativo=True).count(), 1)
        r = self.as_user(self.u1).delete(self.url + "link-convite/")
        self.assertIsNone(r.json()["link_convite"])
        self.assertEqual(self.as_user(self.u3).post(f"/api/convites/{novo['token']}/aceitar/").status_code, 400)

    def test_so_o_criador_gera_e_ve_o_link(self):
        self.gerar()
        ParticipanteEquipe.objects.create(user=self.u2, equipe=self.equipe)
        self.assertIsNone(self.as_user(self.u2).get("/api/me/equipes/").json()[0]["link_convite"])
        self.assertEqual(self.as_user(self.u2).post(self.url + "link-convite/").status_code, 403)

    def test_info_publica_e_aceite(self):
        token = self.gerar()["token"]
        self.client.force_authenticate(user=None)
        info = self.client.get(f"/api/convites/{token}/").json()
        self.assertTrue(info["valido"])
        self.assertEqual(info["equipe"], "Alfa")
        self.assertEqual(self.as_user(self.u3).post(f"/api/convites/{token}/aceitar/").status_code, 200)
        self.assertTrue(ParticipanteEquipe.objects.filter(user=self.u3, equipe=self.equipe).exists())
        # já está numa equipe da edição
        self.assertEqual(self.as_user(self.u3).post(f"/api/convites/{token}/aceitar/").status_code, 400)
        self.assertEqual(self.client.get("/api/convites/inexistente/").status_code, 404)

    def test_reutilizavel_ate_lotar(self):
        token = self.gerar()["token"]  # máximo 3
        ParticipanteEquipe.objects.create(user=self.u2, equipe=self.equipe)
        self.assertEqual(self.as_user(self.u3).post(f"/api/convites/{token}/aceitar/").status_code, 200)
        r = self.as_user(self.u4).post(f"/api/convites/{token}/aceitar/")
        self.assertEqual(r.status_code, 400)
        self.client.force_authenticate(user=None)
        self.assertFalse(self.client.get(f"/api/convites/{token}/").json()["valido"])

    def test_nao_participante_e_fora_das_inscricoes(self):
        token = self.gerar()["token"]
        self.assertEqual(self.as_user(self.aval).post(f"/api/convites/{token}/aceitar/").status_code, 403)
        self.edicao.status = "EM_ANDAMENTO"
        self.edicao.save()
        self.assertEqual(self.as_user(self.u3).post(f"/api/convites/{token}/aceitar/").status_code, 400)
        self.client.force_authenticate(user=None)
        self.assertFalse(self.client.get(f"/api/convites/{token}/").json()["valido"])
