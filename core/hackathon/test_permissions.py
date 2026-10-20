from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from .models import (
    User, TipoEdicao, Edicao, Projeto, Criterio, AvaliadorEdicao, Nota,
)
from .models.user import tipoUser


class PermissionsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        mk = User.objects.create_user
        self.admin = mk(username='adm', email='adm@t.com', password='x', tipoUser=tipoUser.admin)
        self.part = mk(username='part', email='part@t.com', password='x', tipoUser=tipoUser.participante)
        self.part2 = mk(username='part2', email='part2@t.com', password='x', tipoUser=tipoUser.participante)
        self.aval = mk(username='aval', email='aval@t.com', password='x', tipoUser=tipoUser.avaliador)
        self.aval2 = mk(username='aval2', email='aval2@t.com', password='x', tipoUser=tipoUser.avaliador)

        self.tipo_edicao = TipoEdicao.objects.create(nome='Presencial')
        self.edicao = Edicao.objects.create(
            nome='Hack', ano=2026, status='AVALIACAO',
            data_inicio=date.today(), data_fim=date.today() + timedelta(days=3),
            minimo_participantes=2, maximo_participantes=5, maximo_equipes=10,
            tipo_edicao=self.tipo_edicao,
        )
        self.projeto = Projeto.objects.create(
            nome_projeto='P', descricao_projeto='D', edicao=self.edicao,
            link_deploy_projeto='https://p.example.com',
        )
        self.c1 = Criterio.objects.create(nome='C1', edicao=self.edicao)
        self.c2 = Criterio.objects.create(nome='C2', edicao=self.edicao)
        self.ae = AvaliadorEdicao.objects.create(avaliador=self.aval, edicao=self.edicao)
        self.ae2 = AvaliadorEdicao.objects.create(avaliador=self.aval2, edicao=self.edicao)

    def as_user(self, user):
        self.client.force_authenticate(user=user)
        return self.client


class UserViewSetPermissionTests(PermissionsTestCase):
    def test_anonimo_negado(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/users/').status_code, 401)

    def test_listagem_apenas_admin(self):
        self.assertEqual(self.as_user(self.admin).get('/api/users/').status_code, 200)
        for u in (self.part, self.aval):
            self.assertEqual(self.as_user(u).get('/api/users/').status_code, 403)

    def test_criacao_apenas_admin(self):
        payload = {'username': 'n', 'email': 'n@t.com', 'password': 'senha12345', 'tipoUser': 'PARTICIPANTE'}
        self.assertEqual(self.as_user(self.part).post('/api/users/', payload, format='json').status_code, 403)
        self.assertEqual(self.as_user(self.admin).post('/api/users/', payload, format='json').status_code, 201)

    def test_exclusao_apenas_admin(self):
        self.assertEqual(self.as_user(self.part).delete(f'/api/users/{self.part2.id}/').status_code, 403)
        self.assertEqual(self.as_user(self.part).delete(f'/api/users/{self.part.id}/').status_code, 403)
        self.assertEqual(self.as_user(self.admin).delete(f'/api/users/{self.part2.id}/').status_code, 204)

    def test_usuario_ve_e_edita_a_si_mesmo(self):
        c = self.as_user(self.part)
        self.assertEqual(c.get(f'/api/users/{self.part.id}/').status_code, 200)
        r = c.patch(f'/api/users/{self.part.id}/', {'first_name': 'Novo'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.part.refresh_from_db()
        self.assertEqual(self.part.first_name, 'Novo')

    def test_usuario_nao_acessa_outro(self):
        c = self.as_user(self.part)
        self.assertEqual(c.get(f'/api/users/{self.part2.id}/').status_code, 403)
        self.assertEqual(c.patch(f'/api/users/{self.part2.id}/', {'first_name': 'X'}, format='json').status_code, 403)

    def test_usuario_nao_altera_proprio_tipo(self):
        for user, novo in ((self.part, 'ADMIN'), (self.aval, 'PARTICIPANTE'), (self.part, 'AVALIADOR')):
            r = self.as_user(user).patch(f'/api/users/{user.id}/', {'tipoUser': novo}, format='json')
            self.assertEqual(r.status_code, 400, (user, novo))
            user.refresh_from_db()
            self.assertNotEqual(user.tipoUser, novo)

    def test_admin_altera_tipo(self):
        r = self.as_user(self.admin).patch(f'/api/users/{self.part.id}/', {'tipoUser': 'AVALIADOR'}, format='json')
        self.assertEqual(r.status_code, 200)


class ReadOnlyForNonAdminTests(PermissionsTestCase):
    def test_leitura_para_autenticados(self):
        for url in ('edicoes', 'projetos', 'criterios', 'temas', 'equipes', 'apoiadores',
                    'tipos-edicao', 'participantes-equipe', 'avaliadores', 'notas'):
            for u in (self.part, self.aval, self.admin):
                self.assertEqual(self.as_user(u).get(f'/api/{url}/').status_code, 200, (url, u))

    def test_escrita_negada_para_nao_admin(self):
        for u in (self.part, self.aval):
            c = self.as_user(u)
            self.assertEqual(c.post('/api/tipos-edicao/', {'nome': 'X'}, format='json').status_code, 403)
            self.assertEqual(c.patch(f'/api/edicoes/{self.edicao.id}/', {'nome': 'Y'}, format='json').status_code, 403)
            self.assertEqual(c.delete(f'/api/projetos/{self.projeto.id}/').status_code, 403)
            self.assertEqual(c.delete(f'/api/criterios/{self.c1.id}/').status_code, 403)

    def test_escrita_permitida_para_admin(self):
        c = self.as_user(self.admin)
        self.assertEqual(c.post('/api/tipos-edicao/', {'nome': 'Online'}, format='json').status_code, 201)
        self.assertEqual(c.patch(f'/api/criterios/{self.c1.id}/', {'nome': 'Novo'}, format='json').status_code, 200)


class NotaPermissionTests(PermissionsTestCase):
    def payload(self, avaliador, criterio):
        return {'avaliador': avaliador.id, 'projeto': self.projeto.id, 'criterio': criterio.id, 'nota': '8.00'}

    def test_avaliador_cria_propria_nota(self):
        r = self.as_user(self.aval).post('/api/notas/', self.payload(self.ae, self.c1), format='json')
        self.assertEqual(r.status_code, 201)

    def test_avaliador_nao_cria_nota_em_nome_de_outro(self):
        r = self.as_user(self.aval).post('/api/notas/', self.payload(self.ae2, self.c1), format='json')
        self.assertEqual(r.status_code, 403)

    def test_participante_e_admin_nao_escrevem_notas(self):
        for u in (self.part, self.admin):
            r = self.as_user(u).post('/api/notas/', self.payload(self.ae, self.c1), format='json')
            self.assertEqual(r.status_code, 403, u)

    def test_lote_somente_do_proprio_avaliador(self):
        body = lambda ae: {'avaliador': ae.id, 'projeto': self.projeto.id,
                           'notas': [{'criterio': self.c1.id, 'nota': '7.00'}]}
        self.assertEqual(self.as_user(self.aval).post('/api/notas/lote/', body(self.ae2), format='json').status_code, 403)
        self.assertEqual(self.as_user(self.aval).post('/api/notas/lote/', body(self.ae), format='json').status_code, 201)

    def test_edicao_e_exclusao_somente_do_dono(self):
        nota = Nota.objects.create(nota='5.00', projeto=self.projeto, criterio=self.c1, avaliador=self.ae)
        url = f'/api/notas/{nota.id}/'
        # Notas de outros avaliadores nem aparecem no queryset: 404 (não vaza a existência).
        self.assertEqual(self.as_user(self.aval2).patch(url, {'nota': '9.00'}, format='json').status_code, 404)
        self.assertEqual(self.as_user(self.aval2).delete(url).status_code, 404)
        self.assertEqual(self.as_user(self.admin).delete(url).status_code, 403)
        self.assertEqual(self.as_user(self.aval).patch(url, {'nota': '9.00'}, format='json').status_code, 200)
        self.assertEqual(self.as_user(self.aval).delete(url).status_code, 204)
