import json
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle

from .models import (
    Apoiador, Criterio, Edicao, Equipe, Projeto, Tema, TipoEdicao, User,
)
from .models.user import tipoUser

PUBLIC_LISTS = ['edicoes', 'tipos-edicao', 'apoiadores', 'temas', 'criterios', 'projetos', 'equipes']
PRIVATE_LISTS = ['users', 'participantes-equipe', 'avaliadores', 'notas']
FORBIDDEN_KEYS = {'email', 'username', 'password', 'participantes', 'user', 'users', 'first_name', 'last_name'}


def all_keys(data):
    if isinstance(data, dict):
        for key, value in data.items():
            yield key
            yield from all_keys(value)
    elif isinstance(data, list):
        for item in data:
            yield from all_keys(item)


class PublicApiTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.tipo = TipoEdicao.objects.create(nome='Presencial')
        self.tipo2 = TipoEdicao.objects.create(nome='Online')
        self.apoiador = Apoiador.objects.create(nome='TechCorp', tipo='ouro')
        self.edicao = self.make_edicao('Hack Alpha', 2026, 'INSCRICAO', date(2026, 5, 1))
        self.criterio = Criterio.objects.create(nome='Inovação', edicao=self.edicao)
        self.tema = Tema.objects.create(descricao_tema='Saúde', edicao=self.edicao)
        self.projeto = Projeto.objects.create(
            nome_projeto='App Vida', descricao_projeto='D', edicao=self.edicao,
            link_deploy_projeto='https://vida.example.com', notaFinal_projeto=Decimal('9.50'),
        )
        self.equipe = Equipe.objects.create(
            nome_equipe='Alpha', edicao=self.edicao, tema=self.tema, projeto=self.projeto,
        )
        self.user = User.objects.create_user(
            username='joao', email='joao@t.com', password='x', tipoUser=tipoUser.participante,
        )
        self.admin = User.objects.create_user(
            username='adm', email='adm@t.com', password='x', tipoUser=tipoUser.admin,
        )

    def make_edicao(self, nome, ano, status, inicio, tipo=None):
        edicao = Edicao.objects.create(
            nome=nome, ano=ano, status=status, data_inicio=inicio,
            data_fim=inicio + timedelta(days=3), minimo_participantes=2,
            maximo_participantes=5, maximo_equipes=10, tipo_edicao=tipo or self.tipo,
            local='Sala 1', responsavel='Fulano',
        )
        edicao.apoiadores.add(self.apoiador)
        return edicao

    def finalizar(self):
        self.edicao.status = 'FINALIZADO'
        self.edicao.save()


class AcessoPublicoTests(PublicApiTestCase):
    def test_get_sem_token_retorna_200(self):
        for rota in PUBLIC_LISTS:
            self.assertEqual(self.client.get(f'/api/{rota}/').status_code, 200, rota)
        self.assertEqual(self.client.get(f'/api/edicoes/{self.edicao.id}/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/equipes/{self.equipe.id}/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/projetos/{self.projeto.id}/').status_code, 200)

    def test_rotas_privadas_exigem_token(self):
        for rota in PRIVATE_LISTS:
            self.assertEqual(self.client.get(f'/api/{rota}/').status_code, 401, rota)

    def test_escrita_sem_token_retorna_401(self):
        for rota in PUBLIC_LISTS:
            self.assertEqual(self.client.post(f'/api/{rota}/', {}, format='json').status_code, 401, rota)
        urls = [
            f'/api/edicoes/{self.edicao.id}/',
            f'/api/equipes/{self.equipe.id}/',
            f'/api/projetos/{self.projeto.id}/',
            f'/api/criterios/{self.criterio.id}/',
        ]
        for url in urls:
            self.assertEqual(self.client.patch(url, {}, format='json').status_code, 401, url)
            self.assertEqual(self.client.delete(url).status_code, 401, url)

    def test_escrita_de_nao_admin_continua_negada(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.patch(f'/api/edicoes/{self.edicao.id}/', {'nome': 'X'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_respostas_publicas_sem_dados_pessoais(self):
        from .models import ParticipanteEquipe
        ParticipanteEquipe.objects.create(user=self.user, equipe=self.equipe)
        urls = [f'/api/{r}/' for r in PUBLIC_LISTS] + [
            f'/api/edicoes/{self.edicao.id}/',
            f'/api/equipes/{self.equipe.id}/',
            f'/api/projetos/{self.projeto.id}/',
        ]
        for url in urls:
            body = self.client.get(url).json()
            self.assertFalse(FORBIDDEN_KEYS & set(all_keys(body)), url)
            self.assertNotIn('joao@t.com', json.dumps(body), url)


class ContratoTests(PublicApiTestCase):
    def test_lista_de_edicoes(self):
        item = self.client.get('/api/edicoes/').json()['results'][0]
        self.assertEqual(item, {
            'id': self.edicao.id, 'nome': 'Hack Alpha', 'ano': 2026, 'status': 'INSCRICAO',
            'status_label': 'Inscrição', 'data_inicio': '2026-05-01', 'data_fim': '2026-05-04',
            'local': 'Sala 1', 'responsavel': 'Fulano', 'imagem_capa': None, 'tipo_edicao': 'Presencial',
            'total_equipes': 1,
        })

    def test_detalhe_da_edicao(self):
        body = self.client.get(f'/api/edicoes/{self.edicao.id}/').json()
        self.assertEqual(body['apoiadores'], [
            {'id': self.apoiador.id, 'nome': 'TechCorp', 'tipo': 'ouro', 'logo_apoiador': None}
        ])
        self.assertEqual(body['criterios'], [{'id': self.criterio.id, 'nome': 'Inovação'}])
        self.assertEqual(body['temas'], [{'id': self.tema.id, 'descricao_tema': 'Saúde'}])
        self.assertEqual(body['maximo_equipes'], 10)
        equipe = body['equipes'][0]
        self.assertEqual(equipe['tema'], 'Saúde')
        self.assertEqual(equipe['projeto']['nome_projeto'], 'App Vida')
        self.assertEqual(body['total_equipes'], 1)

    def test_projeto_publico(self):
        body = self.client.get(f'/api/projetos/{self.projeto.id}/').json()
        self.assertEqual(body['nome_equipe'], 'Alpha')
        self.assertEqual(body['edicao'], self.edicao.id)

    def test_projeto_sem_equipe(self):
        sem = Projeto.objects.create(nome_projeto='Solto', descricao_projeto='D', edicao=self.edicao)
        body = self.client.get(f'/api/projetos/{sem.id}/').json()
        self.assertIsNone(body['nome_equipe'])

    def test_escrita_aceita_local_e_responsavel(self):
        self.client.force_authenticate(user=self.admin)
        r = self.client.patch(
            f'/api/edicoes/{self.edicao.id}/', {'local': 'Auditório', 'responsavel': 'Beltrano'}, format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['local'], 'Auditório')
        self.assertEqual(r.json()['responsavel'], 'Beltrano')


class NotaFinalTests(PublicApiTestCase):
    def test_nota_oculta_fora_de_finalizado(self):
        for status in ('INSCRICAO', 'EM_ANDAMENTO', 'AVALIACAO'):
            Edicao.objects.filter(pk=self.edicao.pk).update(status=status)
            self.assertIsNone(self.client.get(f'/api/projetos/{self.projeto.id}/').json()['nota_final'], status)
            self.assertIsNone(self.client.get('/api/projetos/').json()['results'][0]['nota_final'], status)
            self.assertIsNone(self.client.get('/api/equipes/').json()['results'][0]['projeto']['nota_final'], status)
            detalhe = self.client.get(f'/api/edicoes/{self.edicao.id}/').json()
            self.assertIsNone(detalhe['equipes'][0]['projeto']['nota_final'], status)

    def test_nota_aparece_em_finalizado(self):
        self.finalizar()
        self.assertEqual(self.client.get(f'/api/projetos/{self.projeto.id}/').json()['nota_final'], '9.50')
        self.assertEqual(self.client.get('/api/equipes/').json()['results'][0]['projeto']['nota_final'], '9.50')
        detalhe = self.client.get(f'/api/edicoes/{self.edicao.id}/').json()
        self.assertEqual(detalhe['equipes'][0]['projeto']['nota_final'], '9.50')


class FiltrosTests(PublicApiTestCase):
    def setUp(self):
        super().setUp()
        self.e2 = self.make_edicao('Hack Beta', 2025, 'FINALIZADO', date(2025, 3, 1), tipo=self.tipo2)
        self.e3 = self.make_edicao('Maratona', 2024, 'AVALIACAO', date(2024, 8, 1))

    def nomes(self, query):
        r = self.client.get(f'/api/edicoes/?{query}')
        self.assertEqual(r.status_code, 200)
        return [e['nome'] for e in r.json()['results']]

    def test_filtros_de_edicao(self):
        self.assertEqual(self.nomes('status=FINALIZADO'), ['Hack Beta'])
        self.assertEqual(self.nomes('ano=2024'), ['Maratona'])
        self.assertEqual(self.nomes(f'tipo_edicao={self.tipo2.id}'), ['Hack Beta'])
        self.assertEqual(sorted(self.nomes('search=hack')), ['Hack Alpha', 'Hack Beta'])

    def test_ordenacao_de_edicao(self):
        self.assertEqual(self.nomes('ordering=data_inicio'), ['Maratona', 'Hack Beta', 'Hack Alpha'])
        self.assertEqual(self.nomes('ordering=-data_inicio'), ['Hack Alpha', 'Hack Beta', 'Maratona'])
        self.assertEqual(self.nomes('ordering=nome'), ['Hack Alpha', 'Hack Beta', 'Maratona'])

    def test_valores_invalidos_nao_geram_500(self):
        for query in ('status=XYZ', 'ano=abc', 'tipo_edicao=x', 'ano=99999999999999999999'):
            self.assertEqual(self.client.get(f'/api/edicoes/?{query}').status_code, 400, query)
        self.assertEqual(self.nomes('ano=1900'), [])
        self.assertEqual(self.client.get('/api/edicoes/?ordering=campo_inexistente').status_code, 200)
        for rota in ('projetos', 'equipes'):
            self.assertEqual(self.client.get(f'/api/{rota}/?edicao=abc').status_code, 400)
            self.assertEqual(self.client.get(f'/api/{rota}/?edicao=9999').json()['results'], [])
        self.assertEqual(self.client.get('/api/temas/?edicao_id=abc').status_code, 400)

    def test_filtros_de_projeto_e_equipe(self):
        for rota, busca in (('projetos', 'Vida'), ('equipes', 'Alpha')):
            r = self.client.get(f'/api/{rota}/?edicao={self.edicao.id}&search={busca}').json()
            self.assertEqual(r['count'], 1, rota)
            self.assertEqual(self.client.get(f'/api/{rota}/?edicao={self.e2.id}').json()['count'], 0)
            self.assertEqual(self.client.get(f'/api/{rota}/?search=zzz').json()['count'], 0)

    def test_ordenacao_de_projetos(self):
        Projeto.objects.create(nome_projeto='Zeta', descricao_projeto='D', edicao=self.edicao)
        nomes = [p['nome_projeto'] for p in self.client.get('/api/projetos/?ordering=-nome_projeto').json()['results']]
        self.assertEqual(nomes, ['Zeta', 'App Vida'])


class PaginacaoTests(PublicApiTestCase):
    def setUp(self):
        super().setUp()
        for i in range(11):
            self.make_edicao(f'Extra {i:02d}', 2020, 'INSCRICAO', date(2020, 1, 1) + timedelta(days=i))

    def test_formato_e_tamanho_padrao(self):
        body = self.client.get('/api/edicoes/').json()
        self.assertEqual(set(body), {'count', 'next', 'previous', 'results'})
        self.assertEqual(body['count'], 12)
        self.assertEqual(len(body['results']), 8)
        self.assertIsNone(body['previous'])
        self.assertIsNotNone(body['next'])

    def test_segunda_pagina_e_page_size(self):
        self.assertEqual(len(self.client.get('/api/edicoes/?page=2').json()['results']), 4)
        self.assertEqual(len(self.client.get('/api/edicoes/?page_size=3').json()['results']), 3)
        self.assertEqual(len(self.client.get('/api/edicoes/?page_size=1000').json()['results']), 12)
        self.assertEqual(self.client.get('/api/edicoes/?page=99').status_code, 404)


class RankingTests(PublicApiTestCase):
    def test_403_antes_de_finalizar(self):
        for status in ('INSCRICAO', 'EM_ANDAMENTO', 'AVALIACAO'):
            Edicao.objects.filter(pk=self.edicao.pk).update(status=status)
            r = self.client.get(f'/api/edicoes/{self.edicao.id}/ranking/')
            self.assertEqual(r.status_code, 403, status)
            self.assertIn('finalizada', r.json()['detail'])

    def test_ranking_ordenado_apos_finalizar(self):
        p2 = Projeto.objects.create(
            nome_projeto='Outro', descricao_projeto='D', edicao=self.edicao, notaFinal_projeto=Decimal('9.50'))
        p3 = Projeto.objects.create(
            nome_projeto='Melhor', descricao_projeto='D', edicao=self.edicao, notaFinal_projeto=Decimal('10.00'))
        Projeto.objects.create(nome_projeto='Sem nota', descricao_projeto='D', edicao=self.edicao)
        tema = Tema.objects.create(descricao_tema='Edu', edicao=self.edicao)
        Equipe.objects.create(nome_equipe='Beta', edicao=self.edicao, tema=tema, projeto=p3)
        self.finalizar()
        r = self.client.get(f'/api/edicoes/{self.edicao.id}/ranking/')
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual([i['projeto'] for i in body], ['Melhor', 'App Vida', 'Outro'])
        self.assertEqual([i['posicao'] for i in body], [1, 2, 2])
        self.assertEqual(body[0]['equipe'], 'Beta')
        self.assertEqual(body[0]['nota_final'], '10.00')
        self.assertIsNone(body[2]['equipe'])
        self.assertFalse(FORBIDDEN_KEYS & set(all_keys(body)))

    def test_ranking_de_edicao_inexistente(self):
        self.assertEqual(self.client.get('/api/edicoes/9999/ranking/').status_code, 404)


class CorsTests(PublicApiTestCase):
    def test_origem_permitida(self):
        r = self.client.get('/api/edicoes/', HTTP_ORIGIN='http://localhost:5173')
        self.assertEqual(r['Access-Control-Allow-Origin'], 'http://localhost:5173')

    def test_origem_nao_permitida(self):
        r = self.client.get('/api/edicoes/', HTTP_ORIGIN='http://malicioso.example.com')
        self.assertNotIn('Access-Control-Allow-Origin', r)


class DesempenhoTests(PublicApiTestCase):
    def test_detalhe_da_edicao_tem_numero_fixo_de_consultas(self):
        def consultas():
            with self.assertNumQueries(5):
                self.assertEqual(self.client.get(f'/api/edicoes/{self.edicao.id}/').status_code, 200)

        consultas()
        for i in range(5):
            projeto = Projeto.objects.create(nome_projeto=f'P{i}', descricao_projeto='D', edicao=self.edicao)
            tema = Tema.objects.create(descricao_tema=f'T{i}', edicao=self.edicao)
            Equipe.objects.create(nome_equipe=f'E{i}', edicao=self.edicao, tema=tema, projeto=projeto)
            Criterio.objects.create(nome=f'C{i}', edicao=self.edicao)
        consultas()

    def test_listas_sem_n_mais_um(self):
        for i in range(5):
            self.make_edicao(f'E{i}', 2020, 'INSCRICAO', date(2020, 1, 1))
        with self.assertNumQueries(2):  # contagem da paginação + página
            self.client.get('/api/edicoes/')

    def test_limite_para_anonimos(self):
        with mock.patch.dict(AnonRateThrottle.THROTTLE_RATES, {'anon': '2/min'}):
            codigos = [self.client.get('/api/edicoes/').status_code for _ in range(3)]
        self.assertEqual(codigos, [200, 200, 429])


class HealthCheckTests(TestCase):
    def test_health_publico(self):
        resp = self.client.get("/api/health/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})
