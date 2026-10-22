from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import (
    AvaliadorEdicao, Criterio, Edicao, Equipe, Nota, ParticipanteEquipe, Projeto,
    SolicitacaoPerfil, Tema, TipoEdicao, User,
)
from .models.user import tipoUser

SENHA_FORTE = 'Senha-muito-forte-123'


class Base(TestCase):
    def setUp(self):
        self.client = APIClient()
        mk = User.objects.create_user
        self.admin = mk(username='adm', email='adm@t.com', password='x', tipoUser=tipoUser.admin)
        self.prof = mk(username='prof', email='prof@t.com', password='x', tipoUser=tipoUser.professor)
        self.aval = mk(username='aval', email='aval@t.com', password='x', tipoUser=tipoUser.avaliador)
        self.aval2 = mk(username='aval2', email='aval2@t.com', password='x', tipoUser=tipoUser.avaliador)
        self.u1 = mk(username='u1', email='u1@t.com', password='x')
        self.u2 = mk(username='u2', email='u2@t.com', password='x')
        self.u3 = mk(username='u3', email='u3@t.com', password='x')
        self.u4 = mk(username='u4', email='u4@t.com', password='x')

        self.tipo = TipoEdicao.objects.create(nome='Presencial')
        self.edicao = self.nova_edicao('Hack', maximo_equipes=10)
        self.tema = Tema.objects.create(descricao_tema='Educação', edicao=self.edicao)

    def nova_edicao(self, nome, status='INSCRICAO', **kw):
        dados = dict(
            nome=nome, ano=2026, status=status, data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=3), minimo_participantes=2,
            maximo_participantes=3, maximo_equipes=10, tipo_edicao=self.tipo,
        )
        dados.update(kw)
        return Edicao.objects.create(**dados)

    def as_user(self, user):
        self.client.force_authenticate(user=user)
        return self.client

    def payload(self, **kw):
        corpo = {
            'edicao': self.edicao.id, 'nome_equipe': 'Alfa', 'tema': self.tema.id,
            'projeto': {'nome_projeto': 'App', 'descricao_projeto': 'Desc'},
            'membros': ['u2@t.com'],
        }
        corpo.update(kw)
        return corpo

    def inscrever(self, user=None, **kw):
        return self.as_user(user or self.u1).post('/api/inscricoes/', self.payload(**kw), format='json')

    def criar_equipe(self, nome, criador, outros=(), edicao=None):
        edicao = edicao or self.edicao
        tema = Tema.objects.get_or_create(descricao_tema='T', edicao=edicao)[0]
        projeto = Projeto.objects.create(nome_projeto=f'P-{nome}', descricao_projeto='D', edicao=edicao)
        equipe = Equipe.objects.create(nome_equipe=nome, edicao=edicao, tema=tema, projeto=projeto, criador=criador)
        for u in (criador, *outros):
            ParticipanteEquipe.objects.create(user=u, equipe=equipe)
        return equipe


class RegistroETest(Base):
    def corpo(self, **kw):
        c = {'email': 'novo@t.com', 'password': SENHA_FORTE, 'first_name': 'Novo'}
        c.update(kw)
        return c

    def test_cadastro_publico_cria_participante(self):
        self.client.force_authenticate(user=None)
        r = self.client.post('/api/auth/registro/', self.corpo(tipoUser='ADMIN'), format='json')
        self.assertEqual(r.status_code, 201, r.content)
        u = User.objects.get(email='novo@t.com')
        self.assertEqual(u.tipoUser, tipoUser.participante)
        self.assertTrue(u.check_password(SENHA_FORTE))
        self.assertFalse(SolicitacaoPerfil.objects.exists())
        self.assertNotIn('password', r.json())

    def test_email_unico_e_senha_validada(self):
        self.client.post('/api/auth/registro/', self.corpo(), format='json')
        r = self.client.post('/api/auth/registro/', self.corpo(username='outro', email='NOVO@t.com'), format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('email', r.json())
        r = self.client.post('/api/auth/registro/', self.corpo(email='x@t.com', password='123'), format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('password', r.json())

    def test_perfil_solicitado_cria_pendencia_sem_mudar_perfil(self):
        for perfil in ('AVALIADOR', 'PROFESSOR'):
            r = self.client.post(
                '/api/auth/registro/',
                self.corpo(email=f'{perfil.lower()}@t.com', perfil_solicitado=perfil), format='json')
            self.assertEqual(r.status_code, 201, r.content)
            u = User.objects.get(email=f'{perfil.lower()}@t.com')
            self.assertEqual(u.tipoUser, tipoUser.participante)
            s = SolicitacaoPerfil.objects.get(usuario=u)
            self.assertEqual((s.perfil_solicitado, s.status), (perfil, 'PENDENTE'))

    def test_perfil_solicitado_invalido(self):
        r = self.client.post('/api/auth/registro/', self.corpo(perfil_solicitado='ADMIN'), format='json')
        self.assertEqual(r.status_code, 400)
        self.assertFalse(User.objects.filter(email='novo@t.com').exists())


class SolicitacaoPerfilTest(Base):
    def setUp(self):
        super().setUp()
        self.sol = SolicitacaoPerfil.objects.create(usuario=self.u1, perfil_solicitado='AVALIADOR')
        self.sol2 = SolicitacaoPerfil.objects.create(usuario=self.u2, perfil_solicitado='PROFESSOR')

    def test_apenas_admin(self):
        for u in (self.u1, self.prof, self.aval):
            c = self.as_user(u)
            self.assertEqual(c.get('/api/solicitacoes-perfil/').status_code, 403)
            self.assertEqual(c.post(f'/api/solicitacoes-perfil/{self.sol.id}/aprovar/').status_code, 403)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/solicitacoes-perfil/').status_code, 401)

    def test_listar_com_filtro(self):
        self.sol2.recusar(self.admin)
        c = self.as_user(self.admin)
        self.assertEqual(c.get('/api/solicitacoes-perfil/').json()['count'], 2)
        self.assertEqual(c.get('/api/solicitacoes-perfil/?status=PENDENTE').json()['count'], 1)
        self.assertEqual(c.get('/api/solicitacoes-perfil/?status=XX').status_code, 400)

    def test_aprovar_muda_perfil_so_depois(self):
        self.u1.refresh_from_db()
        self.assertEqual(self.u1.tipoUser, 'PARTICIPANTE')
        r = self.as_user(self.admin).post(f'/api/solicitacoes-perfil/{self.sol.id}/aprovar/')
        self.assertEqual(r.status_code, 200)
        self.u1.refresh_from_db()
        self.sol.refresh_from_db()
        self.assertEqual(self.u1.tipoUser, 'AVALIADOR')
        self.assertEqual((self.sol.status, self.sol.decidida_por), ('APROVADA', self.admin))
        self.assertIsNotNone(self.sol.decidida_em)

    def test_recusar_mantem_perfil_e_nao_decide_duas_vezes(self):
        c = self.as_user(self.admin)
        self.assertEqual(c.post(f'/api/solicitacoes-perfil/{self.sol2.id}/recusar/').status_code, 200)
        self.u2.refresh_from_db()
        self.assertEqual(self.u2.tipoUser, 'PARTICIPANTE')
        self.assertEqual(c.post(f'/api/solicitacoes-perfil/{self.sol2.id}/aprovar/').status_code, 400)

    def test_acoes_em_massa_do_django_admin(self):
        self.client.force_login(self.admin)
        self.admin.is_staff = self.admin.is_superuser = True
        self.admin.save()
        r = self.client.post('/admin/hackathon/solicitacaoperfil/', {
            'action': 'aprovar_solicitacoes', '_selected_action': [self.sol.id, self.sol2.id],
        })
        self.assertEqual(r.status_code, 302)
        self.u1.refresh_from_db()
        self.u2.refresh_from_db()
        self.assertEqual((self.u1.tipoUser, self.u2.tipoUser), ('AVALIADOR', 'PROFESSOR'))


class PerfilTest(Base):
    def test_ninguem_altera_proprio_tipo(self):
        for user in (self.u1, self.prof, self.aval):
            for novo in ('ADMIN', 'PROFESSOR', 'AVALIADOR', 'PARTICIPANTE'):
                if novo == user.tipoUser:
                    continue
                r = self.as_user(user).patch(f'/api/users/{user.id}/', {'tipoUser': novo}, format='json')
                self.assertEqual(r.status_code, 400, (user, novo))
                user.refresh_from_db()
                self.assertNotEqual(user.tipoUser, novo)

    def test_admin_altera_tipo(self):
        r = self.as_user(self.admin).patch(f'/api/users/{self.u1.id}/', {'tipoUser': 'PROFESSOR'}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_professor_le_tudo_e_nao_escreve(self):
        equipe = self.criar_equipe('E', self.u1, [self.u2])
        c = self.as_user(self.prof)
        self.assertEqual(c.get('/api/equipes/').status_code, 200)
        self.assertEqual(c.get('/api/projetos/').status_code, 200)
        self.assertEqual(c.get('/api/participantes-equipe/').json()['count'], 2)
        self.assertEqual(c.get('/api/notas/').status_code, 200)
        self.assertEqual(c.get('/api/users/').status_code, 403)
        self.assertEqual(c.patch(f'/api/equipes/{equipe.id}/', {'nome_equipe': 'X'}, format='json').status_code, 403)
        self.assertEqual(c.delete(f'/api/projetos/{equipe.projeto_id}/').status_code, 403)
        self.assertEqual(c.post('/api/inscricoes/', self.payload(), format='json').status_code, 403)
        self.assertEqual(c.patch(f'/api/edicoes/{self.edicao.id}/', {'nome': 'X'}, format='json').status_code, 403)
        self.assertEqual(c.post('/api/notas/lote/', {'projeto': equipe.projeto_id, 'notas': []}, format='json').status_code, 403)

    def test_participante_nao_ve_integrantes_de_terceiros(self):
        self.criar_equipe('E1', self.u1, [self.u2])
        self.criar_equipe('E2', self.u3, [self.u4])
        ids = [i['user'] for i in self.as_user(self.u1).get('/api/participantes-equipe/').json()['results']]
        self.assertEqual(sorted(ids), sorted([self.u1.id, self.u2.id]))


class StatusEdicaoTest(Base):
    def patch(self, edicao, status):
        return self.as_user(self.admin).patch(f'/api/edicoes/{edicao.id}/', {'status': status}, format='json')

    def test_avanca_passo_a_passo(self):
        for status in ('EM_ANDAMENTO', 'AVALIACAO', 'FINALIZADO'):
            self.assertEqual(self.patch(self.edicao, status).status_code, 200, status)
            self.edicao.refresh_from_db()
            self.assertEqual(self.edicao.status, status)

    def test_bloqueia_pular_e_voltar(self):
        r = self.patch(self.edicao, 'AVALIACAO')
        self.assertEqual(r.status_code, 400)
        self.assertIn('status', r.json())
        self.patch(self.edicao, 'EM_ANDAMENTO')
        self.assertEqual(self.patch(self.edicao, 'INSCRICAO').status_code, 400)
        self.assertEqual(self.patch(self.edicao, 'FINALIZADO').status_code, 400)

    def test_criacao_somente_em_inscricao(self):
        corpo = {
            'nome': 'N', 'ano': 2027, 'status': 'AVALIACAO', 'data_inicio': '2027-01-01', 'data_fim': '2027-01-03',
            'minimo_participantes': 1, 'maximo_participantes': 3, 'maximo_equipes': 5, 'tipo_edicao': self.tipo.id,
        }
        c = self.as_user(self.admin)
        self.assertEqual(c.post('/api/edicoes/', corpo, format='json').status_code, 400)
        corpo['status'] = 'INSCRICAO'
        self.assertEqual(c.post('/api/edicoes/', corpo, format='json').status_code, 201)

    def test_limites_validados_na_atualizacao(self):
        c = self.as_user(self.admin)
        self.assertEqual(c.patch(f'/api/edicoes/{self.edicao.id}/', {'minimo_participantes': 9}, format='json').status_code, 400)
        self.criar_equipe('E1', self.u1, [self.u2])
        self.criar_equipe('E2', self.u3, [self.u4])
        self.assertEqual(c.patch(f'/api/edicoes/{self.edicao.id}/', {'maximo_equipes': 1}, format='json').status_code, 400)

    def test_finalizada_e_somente_leitura_ate_para_admin(self):
        equipe = self.criar_equipe('E1', self.u1, [self.u2])
        Edicao.objects.filter(pk=self.edicao.pk).update(status='FINALIZADO')
        c = self.as_user(self.admin)
        eid, pid = self.edicao.id, equipe.projeto_id
        vinculo = equipe.participantes.first()
        self.assertEqual(c.patch(f'/api/edicoes/{eid}/', {'nome': 'X'}, format='json').status_code, 403)
        self.assertEqual(c.delete(f'/api/edicoes/{eid}/').status_code, 403)
        self.assertEqual(c.patch(f'/api/equipes/{equipe.id}/', {'nome_equipe': 'X'}, format='json').status_code, 403)
        self.assertEqual(c.delete(f'/api/equipes/{equipe.id}/').status_code, 403)
        self.assertEqual(c.patch(f'/api/projetos/{pid}/', {'nome_projeto': 'X'}, format='json').status_code, 403)
        self.assertEqual(c.delete(f'/api/participantes-equipe/{vinculo.id}/').status_code, 403)
        self.assertEqual(c.post('/api/participantes-equipe/', {'user': self.u3.id, 'equipe': equipe.id}, format='json').status_code, 403)
        self.assertEqual(c.post('/api/projetos/', {'nome_projeto': 'N', 'descricao_projeto': 'D', 'edicao': eid}, format='json').status_code, 403)
        self.assertEqual(c.get(f'/api/edicoes/{eid}/').status_code, 200)

    def test_notas_somente_leitura_na_finalizada(self):
        self.edicao.status = 'AVALIACAO'
        self.edicao.save()
        c1 = Criterio.objects.create(nome='C', edicao=self.edicao)
        ae = AvaliadorEdicao.objects.create(avaliador=self.aval, edicao=self.edicao)
        projeto = Projeto.objects.create(nome_projeto='P', descricao_projeto='D', edicao=self.edicao)
        nota = Nota.objects.create(nota='5.00', projeto=projeto, criterio=c1, avaliador=ae)
        Edicao.objects.filter(pk=self.edicao.pk).update(status='FINALIZADO')
        c = self.as_user(self.aval)
        self.assertEqual(c.patch(f'/api/notas/{nota.id}/', {'nota': '9.00'}, format='json').status_code, 403)
        self.assertEqual(c.delete(f'/api/notas/{nota.id}/').status_code, 403)
        self.assertEqual(c.post('/api/notas/', {'projeto': projeto.id, 'criterio': c1.id, 'nota': '1.00'}, format='json').status_code, 403)


class InscricaoTest(Base):
    def test_cria_equipe_projeto_e_participantes(self):
        r = self.inscrever()
        self.assertEqual(r.status_code, 201, r.content)
        equipe = Equipe.objects.get(nome_equipe='Alfa')
        self.assertEqual(equipe.criador, self.u1)
        self.assertEqual(equipe.projeto.nome_projeto, 'App')
        self.assertEqual(
            sorted(equipe.participantes.values_list('user__email', flat=True)), ['u1@t.com', 'u2@t.com'])
        self.assertEqual(r.json()['projeto']['nota_final'], None)

    def test_exige_autenticacao_e_participante(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post('/api/inscricoes/', self.payload(), format='json').status_code, 401)
        for u in (self.aval, self.admin, self.prof):
            self.assertEqual(self.inscrever(u).status_code, 403)

    def test_edicao_precisa_estar_em_inscricao(self):
        for status in ('EM_ANDAMENTO', 'AVALIACAO', 'FINALIZADO'):
            Edicao.objects.filter(pk=self.edicao.pk).update(status=status)
            r = self.inscrever()
            self.assertEqual(r.status_code, 400, status)
            self.assertIn('edicao', r.json())

    def test_limite_de_equipes(self):
        Edicao.objects.filter(pk=self.edicao.pk).update(maximo_equipes=1)
        self.criar_equipe('Existente', self.u3, [self.u4])
        r = self.inscrever()
        self.assertEqual(r.status_code, 400)
        self.assertIn('limite de 1 equipes', str(r.json()['edicao']))
        self.assertFalse(Equipe.objects.filter(nome_equipe='Alfa').exists())

    def test_minimo_e_maximo_contando_o_criador(self):
        r = self.inscrever(membros=[])
        self.assertEqual(r.status_code, 400)
        self.assertIn('mínimo 2', str(r.json()['membros']).replace('no mínimo', 'mínimo'))
        r = self.inscrever(membros=['u2@t.com', 'u3@t.com', 'u4@t.com'])
        self.assertEqual(r.status_code, 400)
        self.assertIn('máximo 3', str(r.json()['membros']).replace('no máximo', 'máximo'))
        self.assertEqual(self.inscrever(membros=['u2@t.com', 'u3@t.com']).status_code, 201)

    def test_emails_invalidos(self):
        casos = {
            'inexistente@t.com': 'Nenhum usuário cadastrado',
            'aval@t.com': 'não tem perfil de Participante',
            'prof@t.com': 'não tem perfil de Participante',
            'u1@t.com': 'seu próprio e-mail',
        }
        for email, trecho in casos.items():
            r = self.inscrever(membros=[email])
            self.assertEqual(r.status_code, 400, email)
            self.assertIn(trecho, str(r.json()['membros']), email)
        r = self.inscrever(membros=['u2@t.com', 'U2@t.com'])
        self.assertEqual(r.status_code, 400)
        self.assertIn('mais de uma vez', str(r.json()['membros']))
        r = self.inscrever(membros=['não-é-email'])
        self.assertEqual(r.status_code, 400)
        self.assertIn('membros', r.json())

    def test_membro_em_outra_equipe_da_mesma_edicao(self):
        self.criar_equipe('Outra', self.u3, [self.u2])
        r = self.inscrever()
        self.assertEqual(r.status_code, 400)
        self.assertIn("já faz parte da equipe 'Outra'", str(r.json()['membros']))
        # Em outra edição não há conflito.
        outra = self.nova_edicao('Outra ed')
        tema = Tema.objects.create(descricao_tema='X', edicao=outra)
        r = self.inscrever(edicao=outra.id, tema=tema.id)
        self.assertEqual(r.status_code, 201, r.content)

    def test_criador_em_outra_equipe_e_tema_de_outra_edicao(self):
        self.criar_equipe('Outra', self.u1, [self.u3])
        self.assertEqual(self.inscrever().status_code, 400)
        outra = self.nova_edicao('Outra ed')
        tema_outro = Tema.objects.create(descricao_tema='X', edicao=outra)
        r = self.inscrever(user=self.u3, tema=tema_outro.id, nome_equipe='Z')
        self.assertEqual(r.status_code, 400)
        self.assertIn('tema', r.json())

    def test_campos_obrigatorios_por_campo(self):
        r = self.as_user(self.u1).post('/api/inscricoes/', {}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertTrue({'edicao', 'nome_equipe', 'tema', 'projeto'} <= set(r.json()))

    def test_rollback_se_falhar_no_meio(self):
        with mock.patch(
            'core.hackathon.services.inscricao.ParticipanteEquipe.objects.create', side_effect=RuntimeError('boom')
        ):
            with self.assertRaises(RuntimeError):
                self.inscrever()
        self.assertEqual(Equipe.objects.count(), 0)
        self.assertEqual(Projeto.objects.count(), 0)
        self.assertEqual(ParticipanteEquipe.objects.count(), 0)

    def test_nome_de_equipe_repetido(self):
        self.criar_equipe('Alfa', self.u3, [self.u4])
        r = self.inscrever()
        self.assertEqual(r.status_code, 400)
        self.assertIn('nome_equipe', r.json())


class GestaoEquipeTest(Base):
    def setUp(self):
        super().setUp()
        self.equipe = self.criar_equipe('Alfa', self.u1, [self.u2])
        self.url = f'/api/inscricoes/{self.equipe.id}/'

    def test_criador_edita_projeto(self):
        r = self.as_user(self.u1).patch(self.url, {'projeto': {'nome_projeto': 'Novo'}}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.equipe.projeto.refresh_from_db()
        self.assertEqual(self.equipe.projeto.nome_projeto, 'Novo')

    def test_membro_nao_criador_nao_altera(self):
        c = self.as_user(self.u2)
        self.assertEqual(c.patch(self.url, {'nome_equipe': 'X'}, format='json').status_code, 403)
        self.assertEqual(c.delete(self.url).status_code, 403)
        self.assertEqual(c.post(self.url + 'membros/', {'membros': ['u3@t.com']}, format='json').status_code, 403)

    def test_terceiro_nao_enxerga_equipe(self):
        self.assertEqual(self.as_user(self.u3).patch(self.url, {'nome_equipe': 'X'}, format='json').status_code, 404)

    def test_adicionar_e_remover_membros_respeitando_limites(self):
        c = self.as_user(self.u1)
        self.assertEqual(c.post(self.url + 'membros/', {'membros': ['u3@t.com']}, format='json').status_code, 200)
        r = c.post(self.url + 'membros/', {'membros': ['u4@t.com']}, format='json')
        self.assertEqual(r.status_code, 400)  # máximo 3
        self.assertEqual(c.delete(f'{self.url}membros/{self.u3.id}/').status_code, 200)
        r = c.delete(f'{self.url}membros/{self.u2.id}/')
        self.assertEqual(r.status_code, 400)  # mínimo 2
        self.assertEqual(c.delete(f'{self.url}membros/{self.u1.id}/').status_code, 400)  # criador

    def test_membro_pode_sair_se_nao_violar_minimo(self):
        ParticipanteEquipe.objects.create(user=self.u3, equipe=self.equipe)
        self.assertEqual(self.as_user(self.u3).post(self.url + 'sair/').status_code, 204)
        self.assertEqual(self.as_user(self.u2).post(self.url + 'sair/').status_code, 400)
        self.assertEqual(self.as_user(self.u1).post(self.url + 'sair/').status_code, 403)

    def test_criador_exclui_equipe(self):
        self.assertEqual(self.as_user(self.u1).delete(self.url).status_code, 204)
        self.assertFalse(Equipe.objects.exists())
        self.assertFalse(Projeto.objects.exists())
        self.assertFalse(ParticipanteEquipe.objects.exists())

    def test_bloqueado_fora_da_fase_de_inscricao(self):
        Edicao.objects.filter(pk=self.edicao.pk).update(status='EM_ANDAMENTO')
        c = self.as_user(self.u1)
        self.assertEqual(c.patch(self.url, {'nome_equipe': 'X'}, format='json').status_code, 400)
        self.assertEqual(c.delete(self.url).status_code, 400)
        self.assertEqual(c.post(self.url + 'membros/', {'membros': ['u3@t.com']}, format='json').status_code, 400)


class MeTest(Base):
    def setUp(self):
        super().setUp()
        self.equipe = self.criar_equipe('Alfa', self.u1, [self.u2])
        self.equipe.projeto.notaFinal_projeto = Decimal('8.50')
        self.equipe.projeto.save()
        self.outra = self.criar_equipe('Beta', self.u3, [self.u4])

    def test_me(self):
        r = self.as_user(self.u1).get('/api/me/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.json()['email'], r.json()['tipoUser']), ('u1@t.com', 'PARTICIPANTE'))
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/me/').status_code, 401)

    def test_participante_ve_so_as_proprias_equipes_e_projetos(self):
        r = self.as_user(self.u1).get('/api/me/equipes/').json()
        self.assertEqual([e['nome_equipe'] for e in r], ['Alfa'])
        self.assertEqual(sorted(m['email'] for m in r[0]['membros']), ['u1@t.com', 'u2@t.com'])
        self.assertTrue(r[0]['sou_criador'])
        p = self.as_user(self.u1).get('/api/me/projetos/').json()
        self.assertEqual([x['nome_projeto'] for x in p], ['P-Alfa'])
        self.assertNotIn('Beta', str(r) + str(p))

    def test_nota_so_apos_finalizado(self):
        for status in ('INSCRICAO', 'EM_ANDAMENTO', 'AVALIACAO'):
            Edicao.objects.filter(pk=self.edicao.pk).update(status=status)
            self.assertIsNone(self.as_user(self.u1).get('/api/me/projetos/').json()[0]['nota_final'], status)
            self.assertIsNone(self.as_user(self.u1).get('/api/me/equipes/').json()[0]['projeto']['nota_final'], status)
        Edicao.objects.filter(pk=self.edicao.pk).update(status='FINALIZADO')
        self.assertEqual(self.as_user(self.u1).get('/api/me/projetos/').json()[0]['nota_final'], '8.50')

    def test_professor_e_admin_veem_tudo(self):
        for u in (self.prof, self.admin):
            self.assertEqual(len(self.as_user(u).get('/api/me/equipes/').json()), 2)
            self.assertEqual(len(self.as_user(u).get('/api/me/projetos/').json()), 2)

    def test_avaliador_nao_tem_equipes(self):
        self.assertEqual(self.as_user(self.aval).get('/api/me/equipes/').status_code, 403)

    def test_avaliacoes_do_avaliador(self):
        Edicao.objects.filter(pk=self.edicao.pk).update(status='AVALIACAO')
        c1 = Criterio.objects.create(nome='C1', edicao=self.edicao)
        Criterio.objects.create(nome='C2', edicao=self.edicao)
        ae = AvaliadorEdicao.objects.create(avaliador=self.aval, edicao=self.edicao)
        Nota.objects.create(nota='7.00', projeto=self.equipe.projeto, criterio=c1, avaliador=ae)
        outra_ed = self.nova_edicao('Sem vínculo')
        Projeto.objects.create(nome_projeto='Invisível', descricao_projeto='D', edicao=outra_ed)
        itens = self.as_user(self.aval).get('/api/me/avaliacoes/').json()
        self.assertEqual(len(itens), 2)
        alfa = next(i for i in itens if i['projeto']['nome_projeto'] == 'P-Alfa')
        self.assertEqual(len(alfa['criterios_avaliados']), 1)
        self.assertEqual([c['criterio'] for c in alfa['criterios_pendentes']], ['C2'])
        self.assertFalse(alfa['concluido'])
        self.assertTrue(alfa['avaliacao_aberta'])
        self.assertNotIn('Invisível', str(itens))
        self.assertEqual(self.as_user(self.u1).get('/api/me/avaliacoes/').status_code, 403)


class AvaliacaoTest(Base):
    def setUp(self):
        super().setUp()
        Edicao.objects.filter(pk=self.edicao.pk).update(status='AVALIACAO')
        self.edicao.refresh_from_db()
        self.c1 = Criterio.objects.create(nome='C1', edicao=self.edicao)
        self.c2 = Criterio.objects.create(nome='C2', edicao=self.edicao)
        self.ae = AvaliadorEdicao.objects.create(avaliador=self.aval, edicao=self.edicao)
        self.ae2 = AvaliadorEdicao.objects.create(avaliador=self.aval2, edicao=self.edicao)
        self.equipe = self.criar_equipe('Alfa', self.u1, [self.u2])
        self.projeto = self.equipe.projeto

    def lancar(self, user, criterio, nota='8.00', **extra):
        corpo = {'projeto': self.projeto.id, 'criterio': criterio.id, 'nota': nota}
        corpo.update(extra)
        return self.as_user(user).post('/api/notas/', corpo, format='json')

    def test_avaliador_vem_do_usuario_autenticado(self):
        r = self.lancar(self.aval, self.c1)
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['avaliador'], self.ae.id)

    def test_patch_nao_reatribui_avaliador(self):
        nota = Nota.objects.create(nota='5.00', projeto=self.projeto, criterio=self.c1, avaliador=self.ae)
        r = self.as_user(self.aval).patch(
            f'/api/notas/{nota.id}/', {'avaliador': self.ae2.id, 'nota': '6.00'}, format='json')
        self.assertEqual(r.status_code, 200)
        nota.refresh_from_db()
        self.assertEqual(nota.avaliador, self.ae)
        self.assertEqual(nota.nota, Decimal('6.00'))

    def test_so_em_fase_de_avaliacao(self):
        for status in ('INSCRICAO', 'EM_ANDAMENTO'):
            Edicao.objects.filter(pk=self.edicao.pk).update(status=status)
            r = self.lancar(self.aval, self.c1)
            self.assertEqual(r.status_code, 400, status)
            self.assertIn('projeto', r.json())
        r = self.as_user(self.aval).post(
            '/api/notas/lote/', {'projeto': self.projeto.id, 'notas': [{'criterio': self.c1.id, 'nota': '1'}]},
            format='json')
        self.assertEqual(r.status_code, 400)

    def test_avaliador_nao_vinculado_a_edicao(self):
        outro = User.objects.create_user(username='av3', email='av3@t.com', password='x', tipoUser='AVALIADOR')
        r = self.lancar(outro, self.c1)
        self.assertEqual(r.status_code, 400)
        self.assertIn('avaliador', r.json())

    def test_criterio_de_outra_edicao_e_escala(self):
        outra = self.nova_edicao('O', status='AVALIACAO')
        c_outra = Criterio.objects.create(nome='X', edicao=outra)
        self.assertEqual(self.lancar(self.aval, c_outra).status_code, 400)
        self.assertEqual(self.lancar(self.aval, self.c1, nota='10.01').status_code, 400)
        self.assertEqual(self.lancar(self.aval, self.c1, nota='-1').status_code, 400)

    def test_duplicidade_devolve_400(self):
        self.assertEqual(self.lancar(self.aval, self.c1).status_code, 201)
        r = self.lancar(self.aval, self.c1)
        self.assertEqual(r.status_code, 400)
        self.assertIn('já foi avaliado', str(r.json()))

    def test_nota_final_so_com_todos_os_avaliadores_e_criterios(self):
        self.lancar(self.aval, self.c1, '8.00')
        self.lancar(self.aval, self.c2, '6.00')
        self.projeto.refresh_from_db()
        self.assertIsNone(self.projeto.notaFinal_projeto)  # falta o avaliador 2
        self.lancar(self.aval2, self.c1, '10.00')
        self.projeto.refresh_from_db()
        self.assertIsNone(self.projeto.notaFinal_projeto)  # avaliador 2 sem o critério 2
        r = self.lancar(self.aval2, self.c2, '10.00')
        self.projeto.refresh_from_db()
        # 90% da média dos avaliadores ((7 + 10) / 2 = 8,5) + 10% da pré-avaliação (não preenchida = 0)
        self.assertEqual(self.projeto.notaFinal_projeto, Decimal('7.65'))
        Nota.objects.get(pk=r.json()['id']).delete()
        self.projeto.refresh_from_db()
        self.assertIsNone(self.projeto.notaFinal_projeto)

    def test_notas_visiveis_apenas_ao_dono_professor_e_admin(self):
        Nota.objects.create(nota='5.00', projeto=self.projeto, criterio=self.c1, avaliador=self.ae)
        self.assertEqual(self.as_user(self.aval).get('/api/notas/').json()['count'], 1)
        self.assertEqual(self.as_user(self.aval2).get('/api/notas/').json()['count'], 0)
        self.assertEqual(self.as_user(self.u1).get('/api/notas/').json()['count'], 0)
        self.assertEqual(self.as_user(self.prof).get('/api/notas/').json()['count'], 1)
        self.assertEqual(self.as_user(self.admin).get('/api/notas/').json()['count'], 1)

    def test_nota_final_do_projeto_nao_e_editavel_pela_api(self):
        r = self.as_user(self.admin).patch(f'/api/projetos/{self.projeto.id}/', {'notaFinal_projeto': '9.99'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.projeto.refresh_from_db()
        self.assertIsNone(self.projeto.notaFinal_projeto)


class RankingTest(Base):
    def test_ranking_lista_todas_as_equipes_e_empate_divide_posicao(self):
        notas = ['9.00', '9.00', '8.00', '7.00', '6.00', '5.00']
        for i, nota in enumerate(notas):
            equipe = self.criar_equipe(f'E{i}', User.objects.create_user(
                username=f'x{i}', email=f'x{i}@t.com', password='x'))
            Projeto.objects.filter(pk=equipe.projeto_id).update(notaFinal_projeto=Decimal(nota))
        self.assertEqual(self.client.get(f'/api/edicoes/{self.edicao.id}/ranking/').status_code, 403)
        Edicao.objects.filter(pk=self.edicao.pk).update(status='FINALIZADO')
        r = self.client.get(f'/api/edicoes/{self.edicao.id}/ranking/')
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(len(body), 6)
        self.assertEqual([i['posicao'] for i in body], [1, 1, 3, 4, 5, 6])
        self.assertTrue(all(i['equipe'] for i in body))


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class LogoProjetoInscricaoTest(Base):
    def setUp(self):
        super().setUp()
        from .test_imagens import imagem
        self.imagem = imagem
        self.equipe = self.criar_equipe('Alfa', self.u1, [self.u2])
        self.url = f'/api/inscricoes/{self.equipe.id}/logo/'

    def test_criador_envia_troca_e_remove_logo(self):
        c = self.as_user(self.u1)
        r = c.post(self.url, {'logo_projeto': self.imagem()}, format='multipart')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.data['projeto']['logo_projeto'].startswith('http'))
        r = c.post(self.url, {'logo_projeto': self.imagem('JPEG', 'b.jpg')}, format='multipart')
        self.assertEqual(r.status_code, 200, r.content)
        r = c.delete(self.url)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIsNone(r.data['projeto']['logo_projeto'])

    def test_exige_arquivo_e_formato_valido(self):
        c = self.as_user(self.u1)
        self.assertEqual(c.post(self.url, {}, format='multipart').status_code, 400)
        ruim = SimpleUploadedFile('x.png', b'nao e imagem', content_type='image/png')
        self.assertEqual(c.post(self.url, {'logo_projeto': ruim}, format='multipart').status_code, 400)

    def test_nao_criador_e_terceiro_nao_alteram(self):
        self.assertEqual(self.as_user(self.u2).post(self.url, {'logo_projeto': self.imagem()}, format='multipart').status_code, 403)
        self.assertEqual(self.as_user(self.u3).post(self.url, {'logo_projeto': self.imagem()}, format='multipart').status_code, 404)

    def test_bloqueado_fora_da_fase_de_inscricao(self):
        Edicao.objects.filter(pk=self.edicao.pk).update(status='EM_ANDAMENTO')
        r = self.as_user(self.u1).post(self.url, {'logo_projeto': self.imagem()}, format='multipart')
        self.assertEqual(r.status_code, 400)
