from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .models import (
    User,
    Equipe,
    Edicao,
    Tema,
    Projeto,
    TipoEdicao,
    ParticipanteEquipe,
    AvaliadorEdicao,
    Criterio,
    Nota,
)
from .models.user import tipoUser
from .serializers import (
    UserSerializer,
    ParticipanteEquipeSerializer,
    AvaliadorSerializer,
    AvaliadorListSerializer,
    AvaliadorEdicaoSerializer,
    AvaliadorEdicaoListSerializer,
    NotaSerializer,
    NotaListSerializer,
    NotaLoteSerializer,
)
from .views import (
    UserViewSet,
    ParticipanteEquipeViewSet,
    AvaliadorViewSet,
    AvaliadorEdicaoViewSet,
    NotaViewSet,
)


class UserAbstractUserValidationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        # Usuário participante (AbstractUser)
        self.user_participante = User.objects.create_user(
            username='participante',
            email='participante@test.com',
            first_name='Participante Teste',
            password='password123',
            tipoUser=tipoUser.participante
        )

        # Usuário admin (AbstractUser)
        self.user_admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            first_name='Admin Teste',
            password='password123',
            tipoUser=tipoUser.admin
        )

        # Usuário avaliador (AbstractUser)
        self.user_avaliador = User.objects.create_user(
            username='avaliador',
            email='avaliador@test.com',
            first_name='Avaliador Teste',
            password='password123',
            tipoUser=tipoUser.avaliador
        )

    def test_anonymous_cannot_set_admin(self):
        data = {
            'username': 'novouser',
            'first_name': 'Novo User',
            'email': 'novouser@test.com',
            'tipoUser': tipoUser.admin,
            'password': 'password123'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipoUser', serializer.errors)

    def test_anonymous_cannot_set_avaliador(self):
        data = {
            'username': 'novouser',
            'first_name': 'Novo User',
            'email': 'novouser@test.com',
            'tipoUser': tipoUser.avaliador,
            'password': 'password123'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipoUser', serializer.errors)

    def test_participante_cannot_set_admin(self):
        request = self.factory.post('/api/users/')
        force_authenticate(request, user=self.user_participante)

        data = {
            'username': 'novouser',
            'first_name': 'Novo User',
            'email': 'novouser@test.com',
            'tipoUser': tipoUser.admin,
            'password': 'password123'
        }
        serializer = UserSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipoUser', serializer.errors)

    def test_participante_cannot_set_avaliador(self):
        request = self.factory.post('/api/users/')
        force_authenticate(request, user=self.user_participante)

        data = {
            'username': 'novouser',
            'first_name': 'Novo User',
            'email': 'novouser@test.com',
            'tipoUser': tipoUser.avaliador,
            'password': 'password123'
        }
        serializer = UserSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipoUser', serializer.errors)

    def test_participante_can_set_participante(self):
        request = self.factory.post('/api/users/')
        force_authenticate(request, user=self.user_participante)

        data = {
            'username': 'novoparticipante',
            'first_name': 'Novo Participante',
            'email': 'novoparticipante@test.com',
            'tipoUser': tipoUser.participante,
            'password': 'password123'
        }
        serializer = UserSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.tipoUser, tipoUser.participante)
        self.assertTrue(user.check_password('password123'))

    def test_admin_can_set_avaliador_and_admin(self):
        request = self.factory.post('/api/users/')
        force_authenticate(request, user=self.user_admin)

        # Criando como avaliador
        data_avaliador = {
            'username': 'novoavaliador',
            'first_name': 'Novo Avaliador',
            'email': 'novoavaliador@test.com',
            'tipoUser': tipoUser.avaliador,
            'password': 'password123'
        }
        serializer_avaliador = UserSerializer(data=data_avaliador, context={'request': request})
        self.assertTrue(serializer_avaliador.is_valid(), serializer_avaliador.errors)
        avaliador = serializer_avaliador.save()
        self.assertEqual(avaliador.tipoUser, tipoUser.avaliador)

        # Criando como admin
        data_admin = {
            'username': 'novoadmin',
            'first_name': 'Novo Admin',
            'email': 'novoadmin@test.com',
            'tipoUser': tipoUser.admin,
            'password': 'password123'
        }
        serializer_admin = UserSerializer(data=data_admin, context={'request': request})
        self.assertTrue(serializer_admin.is_valid(), serializer_admin.errors)
        admin_user = serializer_admin.save()
        self.assertEqual(admin_user.tipoUser, tipoUser.admin)

    def test_api_viewset_blocks_unauthorized_role_assignment(self):
        view = UserViewSet.as_view({'post': 'create'})
        request = self.factory.post('/api/users/', {
            'username': 'hacker',
            'first_name': 'Hacker',
            'email': 'hacker@test.com',
            'tipoUser': tipoUser.admin,
            'password': 'password123'
        }, format='json')
        force_authenticate(request, user=self.user_participante)

        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('tipoUser', response.data)


class ParticipanteEquipeValidationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        # Usuários com os 3 tipos
        self.user_participante = User.objects.create_user(
            username='participante1',
            email='p1@test.com',
            first_name='Participante 1',
            password='password123',
            tipoUser=tipoUser.participante
        )
        self.user_avaliador = User.objects.create_user(
            username='avaliador1',
            email='av1@test.com',
            first_name='Avaliador 1',
            password='password123',
            tipoUser=tipoUser.avaliador
        )
        self.user_admin = User.objects.create_superuser(
            username='admin1',
            email='adm1@test.com',
            first_name='Admin 1',
            password='password123',
            tipoUser=tipoUser.admin
        )

        # Estrutura base da Edição e Equipe
        self.tipo_edicao = TipoEdicao.objects.create(nome='Presencial')
        self.edicao = Edicao.objects.create(
            nome='Hackathon 2026',
            ano=2026,
            status='INSCRICAO',
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=3),
            minimo_participantes=2,
            maximo_participantes=5,
            maximo_equipes=10,
            tipo_edicao=self.tipo_edicao
        )
        self.tema = Tema.objects.create(
            descricao_tema='Inovação',
            edicao=self.edicao
        )
        self.projeto = Projeto.objects.create(
            nome_projeto='Projeto Alfa',
            edicao=self.edicao,
            link_deploy_projeto='https://alfa.example.com'
        )
        self.equipe = Equipe.objects.create(
            nome_equipe='Equipe Alfa',
            edicao=self.edicao,
            tema=self.tema,
            projeto=self.projeto
        )

    def test_participante_can_be_added_to_equipe_serializer(self):
        data = {
            'user': self.user_participante.id,
            'equipe': self.equipe.id
        }
        serializer = ParticipanteEquipeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        participante_equipe = serializer.save()
        self.assertEqual(participante_equipe.user, self.user_participante)
        self.assertEqual(participante_equipe.equipe, self.equipe)

    def test_avaliador_cannot_be_added_to_equipe_serializer(self):
        data = {
            'user': self.user_avaliador.id,
            'equipe': self.equipe.id
        }
        serializer = ParticipanteEquipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user', serializer.errors)
        self.assertIn('Apenas usuários com perfil de Participante', str(serializer.errors['user']))

    def test_admin_cannot_be_added_to_equipe_serializer(self):
        data = {
            'user': self.user_admin.id,
            'equipe': self.equipe.id
        }
        serializer = ParticipanteEquipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user', serializer.errors)
        self.assertIn('Apenas usuários com perfil de Participante', str(serializer.errors['user']))

    def test_model_clean_prevents_non_participante(self):
        from django.core.exceptions import ValidationError
        pe_avaliador = ParticipanteEquipe(
            user=self.user_avaliador,
            equipe=self.equipe
        )
        with self.assertRaises(ValidationError):
            pe_avaliador.save()

    def test_api_viewset_blocks_non_participante_in_equipe(self):
        view = ParticipanteEquipeViewSet.as_view({'post': 'create'})
        request = self.factory.post('/api/participantes-equipe/', {
            'user': self.user_avaliador.id,
            'equipe': self.equipe.id
        }, format='json')
        force_authenticate(request, user=self.user_participante)

        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('user', response.data)

    def test_user_cannot_join_two_teams_in_same_edicao_serializer(self):
        ParticipanteEquipe.objects.create(user=self.user_participante, equipe=self.equipe)

        projeto2 = Projeto.objects.create(
            nome_projeto='Projeto Beta',
            edicao=self.edicao,
            link_deploy_projeto='https://beta.example.com'
        )
        equipe2 = Equipe.objects.create(
            nome_equipe='Equipe Beta',
            edicao=self.edicao,
            tema=self.tema,
            projeto=projeto2
        )

        data = {
            'user': self.user_participante.id,
            'equipe': equipe2.id
        }
        serializer = ParticipanteEquipeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user', serializer.errors)
        self.assertIn('já faz parte da equipe', str(serializer.errors['user']))

    def test_user_can_join_team_in_different_edicao_serializer(self):
        ParticipanteEquipe.objects.create(user=self.user_participante, equipe=self.equipe)

        edicao2027 = Edicao.objects.create(
            nome='Hackathon 2027',
            ano=2027,
            status='INSCRICAO',
            data_inicio=date.today() + timedelta(days=365),
            data_fim=date.today() + timedelta(days=368),
            minimo_participantes=2,
            maximo_participantes=5,
            maximo_equipes=10,
            tipo_edicao=self.tipo_edicao
        )
        tema2027 = Tema.objects.create(
            descricao_tema='Sustentabilidade',
            edicao=edicao2027
        )
        projeto2027 = Projeto.objects.create(
            nome_projeto='Projeto 2027',
            edicao=edicao2027,
            link_deploy_projeto='https://2027.example.com'
        )
        equipe2027 = Equipe.objects.create(
            nome_equipe='Equipe 2027',
            edicao=edicao2027,
            tema=tema2027,
            projeto=projeto2027
        )

        data = {
            'user': self.user_participante.id,
            'equipe': equipe2027.id
        }
        serializer = ParticipanteEquipeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        pe = serializer.save()
        self.assertEqual(pe.equipe, equipe2027)

    def test_model_clean_prevents_user_in_two_teams_in_same_edicao(self):
        from django.core.exceptions import ValidationError
        ParticipanteEquipe.objects.create(user=self.user_participante, equipe=self.equipe)

        projeto2 = Projeto.objects.create(
            nome_projeto='Projeto Gama',
            edicao=self.edicao,
            link_deploy_projeto='https://gama.example.com'
        )
        equipe2 = Equipe.objects.create(
            nome_equipe='Equipe Gama',
            edicao=self.edicao,
            tema=self.tema,
            projeto=projeto2
        )

        pe2 = ParticipanteEquipe(user=self.user_participante, equipe=equipe2)
        with self.assertRaises(ValidationError) as cm:
            pe2.save()
        self.assertIn('user', cm.exception.message_dict)
        self.assertIn('já faz parte da equipe', str(cm.exception.message_dict['user']))

    def test_api_viewset_blocks_user_in_two_teams_same_edicao(self):
        ParticipanteEquipe.objects.create(user=self.user_participante, equipe=self.equipe)

        projeto2 = Projeto.objects.create(
            nome_projeto='Projeto Delta',
            edicao=self.edicao,
            link_deploy_projeto='https://delta.example.com'
        )
        equipe2 = Equipe.objects.create(
            nome_equipe='Equipe Delta',
            edicao=self.edicao,
            tema=self.tema,
            projeto=projeto2
        )

        view = ParticipanteEquipeViewSet.as_view({'post': 'create'})
        request = self.factory.post('/api/participantes-equipe/', {
            'user': self.user_participante.id,
            'equipe': equipe2.id
        }, format='json')
        force_authenticate(request, user=self.user_participante)

        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('user', response.data)


class AvaliadorEdicaoValidationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user_avaliador = User.objects.create_user(
            username='avaliador_test',
            email='avaliador_test@test.com',
            first_name='Avaliador Test',
            password='password123',
            tipoUser=tipoUser.avaliador
        )
        self.user_participante = User.objects.create_user(
            username='participante_test',
            email='participante_test@test.com',
            first_name='Participante Test',
            password='password123',
            tipoUser=tipoUser.participante
        )
        self.user_admin = User.objects.create_superuser(
            username='admin_test',
            email='admin_test@test.com',
            first_name='Admin Test',
            password='password123',
            tipoUser=tipoUser.admin
        )

        self.tipo_edicao = TipoEdicao.objects.create(nome='Presencial')
        self.edicao1 = Edicao.objects.create(
            nome='Hackathon 2026',
            ano=2026,
            status='INSCRICAO',
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=3),
            minimo_participantes=2,
            maximo_participantes=5,
            maximo_equipes=10,
            tipo_edicao=self.tipo_edicao
        )
        self.edicao2 = Edicao.objects.create(
            nome='Hackathon 2027',
            ano=2027,
            status='INSCRICAO',
            data_inicio=date.today() + timedelta(days=365),
            data_fim=date.today() + timedelta(days=368),
            minimo_participantes=2,
            maximo_participantes=5,
            maximo_equipes=10,
            tipo_edicao=self.tipo_edicao
        )

    def test_avaliador_can_be_linked_to_edicao_serializer(self):
        data = {
            'avaliador': self.user_avaliador.id,
            'edicao': self.edicao1.id
        }
        serializer = AvaliadorSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        avaliador_edicao = serializer.save()
        self.assertEqual(avaliador_edicao.avaliador, self.user_avaliador)
        self.assertEqual(avaliador_edicao.edicao, self.edicao1)

    def test_participante_cannot_be_avaliador_serializer(self):
        data = {
            'avaliador': self.user_participante.id,
            'edicao': self.edicao1.id
        }
        serializer = AvaliadorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('avaliador', serializer.errors)
        self.assertIn('Apenas usuários com perfil de Avaliador', str(serializer.errors['avaliador']))

    def test_admin_cannot_be_avaliador_serializer(self):
        data = {
            'avaliador': self.user_admin.id,
            'edicao': self.edicao1.id
        }
        serializer = AvaliadorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('avaliador', serializer.errors)
        self.assertIn('Apenas usuários com perfil de Avaliador', str(serializer.errors['avaliador']))

    def test_same_avaliador_cannot_be_linked_twice_to_same_edicao(self):
        AvaliadorEdicao.objects.create(avaliador=self.user_avaliador, edicao=self.edicao1)

        data = {
            'avaliador': self.user_avaliador.id,
            'edicao': self.edicao1.id
        }
        serializer = AvaliadorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('já está vinculado como avaliador', str(serializer.errors['non_field_errors']))

    def test_same_avaliador_can_be_linked_to_different_edicoes(self):
        AvaliadorEdicao.objects.create(avaliador=self.user_avaliador, edicao=self.edicao1)

        data = {
            'avaliador': self.user_avaliador.id,
            'edicao': self.edicao2.id
        }
        serializer = AvaliadorSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        av2 = serializer.save()
        self.assertEqual(av2.edicao, self.edicao2)

    def test_model_clean_blocks_invalid_role_and_duplicates(self):
        from django.core.exceptions import ValidationError

        # Bloqueia perfil não avaliador
        av_invalido = AvaliadorEdicao(avaliador=self.user_participante, edicao=self.edicao1)
        with self.assertRaises(ValidationError) as cm:
            av_invalido.save()
        self.assertIn('avaliador', cm.exception.message_dict)

        # Salva válido
        AvaliadorEdicao.objects.create(avaliador=self.user_avaliador, edicao=self.edicao1)

        # Bloqueia duplicado
        av_duplicado = AvaliadorEdicao(avaliador=self.user_avaliador, edicao=self.edicao1)
        with self.assertRaises(ValidationError) as cm:
            av_duplicado.save()
        self.assertIn('avaliador', cm.exception.message_dict)

    def test_avaliador_viewset_crud(self):
        # 1. CREATE (POST)
        view_create = AvaliadorViewSet.as_view({'post': 'create'})
        req_create = self.factory.post('/api/avaliadores/', {
            'avaliador': self.user_avaliador.id,
            'edicao': self.edicao1.id
        }, format='json')
        force_authenticate(req_create, user=self.user_admin)
        res_create = view_create(req_create)
        self.assertEqual(res_create.status_code, 201)
        avaliador_id = res_create.data['id']

        # 2. LIST (GET) - Usa AvaliadorListSerializer
        view_list = AvaliadorViewSet.as_view({'get': 'list'})
        req_list = self.factory.get('/api/avaliadores/')
        force_authenticate(req_list, user=self.user_admin)
        res_list = view_list(req_list)
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(len(res_list.data), 1)
        self.assertEqual(res_list.data[0]['id'], avaliador_id)

        # 3. DETAIL (GET)
        view_detail = AvaliadorViewSet.as_view({'get': 'retrieve'})
        req_detail = self.factory.get(f'/api/avaliadores/{avaliador_id}/')
        force_authenticate(req_detail, user=self.user_admin)
        res_detail = view_detail(req_detail, pk=avaliador_id)
        self.assertEqual(res_detail.status_code, 200)
        self.assertEqual(res_detail.data['avaliador'], self.user_avaliador.id)

        # 4. UPDATE (PATCH)
        view_update = AvaliadorViewSet.as_view({'patch': 'partial_update'})
        req_update = self.factory.patch(f'/api/avaliadores/{avaliador_id}/', {
            'edicao': self.edicao2.id
        }, format='json')
        force_authenticate(req_update, user=self.user_admin)
        res_update = view_update(req_update, pk=avaliador_id)
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.data['edicao'], self.edicao2.id)

        # 5. DELETE (DELETE)
        view_delete = AvaliadorViewSet.as_view({'delete': 'destroy'})
        req_delete = self.factory.delete(f'/api/avaliadores/{avaliador_id}/')
        force_authenticate(req_delete, user=self.user_admin)
        res_delete = view_delete(req_delete, pk=avaliador_id)
        self.assertEqual(res_delete.status_code, 204)
        self.assertFalse(AvaliadorEdicao.objects.filter(pk=avaliador_id).exists())


class NotaValidationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.tipo_edicao = TipoEdicao.objects.create(nome='Presencial')
        self.edicao1 = Edicao.objects.create(
            nome='Hackathon 2026',
            ano=2026,
            status='INSCRICAO',
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=3),
            minimo_participantes=2,
            maximo_participantes=5,
            maximo_equipes=10,
            tipo_edicao=self.tipo_edicao
        )
        self.edicao2 = Edicao.objects.create(
            nome='Hackathon 2027',
            ano=2027,
            status='INSCRICAO',
            data_inicio=date.today() + timedelta(days=365),
            data_fim=date.today() + timedelta(days=368),
            minimo_participantes=2,
            maximo_participantes=5,
            maximo_equipes=10,
            tipo_edicao=self.tipo_edicao
        )

        self.user_avaliador1 = User.objects.create_user(
            username='avaliador1',
            email='av1@test.com',
            first_name='Avaliador 1',
            password='password123',
            tipoUser=tipoUser.avaliador
        )
        self.user_avaliador2 = User.objects.create_user(
            username='avaliador2',
            email='av2@test.com',
            first_name='Avaliador 2',
            password='password123',
            tipoUser=tipoUser.avaliador
        )
        self.user_admin = User.objects.create_superuser(
            username='admin_nota',
            email='admin_nota@test.com',
            first_name='Admin Nota',
            password='password123',
            tipoUser=tipoUser.admin
        )

        self.avaliador_edicao1 = AvaliadorEdicao.objects.create(
            avaliador=self.user_avaliador1,
            edicao=self.edicao1
        )
        self.avaliador_edicao2 = AvaliadorEdicao.objects.create(
            avaliador=self.user_avaliador2,
            edicao=self.edicao2
        )

        self.projeto1 = Projeto.objects.create(
            nome_projeto='Projeto 1',
            descricao_projeto='Descricao 1',
            edicao=self.edicao1,
            link_deploy_projeto='https://proj1.example.com'
        )
        self.projeto2 = Projeto.objects.create(
            nome_projeto='Projeto 2',
            descricao_projeto='Descricao 2',
            edicao=self.edicao2,
            link_deploy_projeto='https://proj2.example.com'
        )

        self.criterio1_ed1 = Criterio.objects.create(
            nome='Inovação',
            edicao=self.edicao1
        )
        self.criterio2_ed1 = Criterio.objects.create(
            nome='Usabilidade',
            edicao=self.edicao1
        )
        self.criterio1_ed2 = Criterio.objects.create(
            nome='Impacto',
            edicao=self.edicao2
        )

    def test_single_nota_creation_success(self):
        view = NotaViewSet.as_view({'post': 'create'})
        payload = {
            'avaliador': self.avaliador_edicao1.id,
            'projeto': self.projeto1.id,
            'criterio': self.criterio1_ed1.id,
            'nota': '8.50',
            'comentario_nota': 'Muito bom'
        }
        request = self.factory.post('/api/notas/', payload, format='json')
        force_authenticate(request, user=self.user_avaliador1)
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['nota'], '8.50')
        self.assertEqual(response.data['avaliador'], self.avaliador_edicao1.id)
        self.assertEqual(response.data['projeto'], self.projeto1.id)

    def test_single_nota_fails_when_avaliador_from_different_edicao(self):
        view = NotaViewSet.as_view({'post': 'create'})
        payload = {
            'avaliador': self.avaliador_edicao2.id,
            'projeto': self.projeto1.id,
            'criterio': self.criterio1_ed1.id,
            'nota': '8.50'
        }
        request = self.factory.post('/api/notas/', payload, format='json')
        force_authenticate(request, user=self.user_avaliador2)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('avaliador', response.data)
        self.assertIn('não pertence à mesma edição', str(response.data['avaliador']))

    def test_single_nota_fails_when_criterio_from_different_edicao(self):
        view = NotaViewSet.as_view({'post': 'create'})
        payload = {
            'avaliador': self.avaliador_edicao1.id,
            'projeto': self.projeto1.id,
            'criterio': self.criterio1_ed2.id,
            'nota': '8.50'
        }
        request = self.factory.post('/api/notas/', payload, format='json')
        force_authenticate(request, user=self.user_avaliador1)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('criterio', response.data)
        self.assertIn('não pertence à mesma edição', str(response.data['criterio']))

    def test_single_nota_fails_duplicate(self):
        Nota.objects.create(
            avaliador=self.avaliador_edicao1,
            projeto=self.projeto1,
            criterio=self.criterio1_ed1,
            nota=Decimal('7.00')
        )
        view = NotaViewSet.as_view({'post': 'create'})
        payload = {
            'avaliador': self.avaliador_edicao1.id,
            'projeto': self.projeto1.id,
            'criterio': self.criterio1_ed1.id,
            'nota': '8.50'
        }
        request = self.factory.post('/api/notas/', payload, format='json')
        force_authenticate(request, user=self.user_avaliador1)
        response = view(request)
        self.assertEqual(response.status_code, 400)

    def test_batch_nota_creation_success(self):
        view = NotaViewSet.as_view({'post': 'lote'})
        payload = {
            'avaliador': self.avaliador_edicao1.id,
            'projeto': self.projeto1.id,
            'notas': [
                {'criterio': self.criterio1_ed1.id, 'nota': '8.50', 'comentario_nota': 'Bom'},
                {'criterio': self.criterio2_ed1.id, 'nota': '9.00'}
            ]
        }
        request = self.factory.post('/api/notas/lote/', payload, format='json')
        force_authenticate(request, user=self.user_avaliador1)
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            Nota.objects.filter(avaliador=self.avaliador_edicao1, projeto=self.projeto1).count(),
            2
        )

    def test_batch_nota_fails_cross_edition_avaliador(self):
        view = NotaViewSet.as_view({'post': 'lote'})
        payload = {
            'avaliador': self.avaliador_edicao2.id,
            'projeto': self.projeto1.id,
            'notas': [
                {'criterio': self.criterio1_ed1.id, 'nota': '8.50'}
            ]
        }
        request = self.factory.post('/api/notas/lote/', payload, format='json')
        force_authenticate(request, user=self.user_avaliador2)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('avaliador', response.data)

    def test_batch_nota_fails_cross_edition_criterio(self):
        view = NotaViewSet.as_view({'post': 'lote'})
        payload = {
            'avaliador': self.avaliador_edicao1.id,
            'projeto': self.projeto1.id,
            'notas': [
                {'criterio': self.criterio1_ed2.id, 'nota': '8.50'}
            ]
        }
        request = self.factory.post('/api/notas/lote/', payload, format='json')
        force_authenticate(request, user=self.user_avaliador1)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('notas', response.data)

    def test_batch_nota_fails_duplicate_criterio_in_payload(self):
        view = NotaViewSet.as_view({'post': 'lote'})
        payload = {
            'avaliador': self.avaliador_edicao1.id,
            'projeto': self.projeto1.id,
            'notas': [
                {'criterio': self.criterio1_ed1.id, 'nota': '8.50'},
                {'criterio': self.criterio1_ed1.id, 'nota': '9.00'}
            ]
        }
        request = self.factory.post('/api/notas/lote/', payload, format='json')
        force_authenticate(request, user=self.user_avaliador1)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('notas', response.data)
        self.assertIn('duplicados', str(response.data['notas']))

    def test_batch_nota_fails_when_criterion_already_evaluated(self):
        Nota.objects.create(
            avaliador=self.avaliador_edicao1,
            projeto=self.projeto1,
            criterio=self.criterio1_ed1,
            nota=Decimal('7.00')
        )
        view = NotaViewSet.as_view({'post': 'lote'})
        payload = {
            'avaliador': self.avaliador_edicao1.id,
            'projeto': self.projeto1.id,
            'notas': [
                {'criterio': self.criterio1_ed1.id, 'nota': '8.50'},
                {'criterio': self.criterio2_ed1.id, 'nota': '9.00'}
            ]
        }
        request = self.factory.post('/api/notas/lote/', payload, format='json')
        force_authenticate(request, user=self.user_avaliador1)
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('notas', response.data)
        self.assertFalse(Nota.objects.filter(avaliador=self.avaliador_edicao1, criterio=self.criterio2_ed1).exists())

    def test_model_clean_validation(self):
        from django.core.exceptions import ValidationError

        # Avaliador de outra edição
        n_invalida1 = Nota(
            avaliador=self.avaliador_edicao2,
            projeto=self.projeto1,
            criterio=self.criterio1_ed1,
            nota=Decimal('8.00')
        )
        with self.assertRaises(ValidationError) as cm:
            n_invalida1.save()
        self.assertIn('avaliador', cm.exception.message_dict)

        # Critério de outra edição
        n_invalida2 = Nota(
            avaliador=self.avaliador_edicao1,
            projeto=self.projeto1,
            criterio=self.criterio1_ed2,
            nota=Decimal('8.00')
        )
        with self.assertRaises(ValidationError) as cm:
            n_invalida2.save()
        self.assertIn('criterio', cm.exception.message_dict)

        # Sucesso
        n_valida = Nota.objects.create(
            avaliador=self.avaliador_edicao1,
            projeto=self.projeto1,
            criterio=self.criterio1_ed1,
            nota=Decimal('8.00')
        )
        self.assertIsNotNone(n_valida.id)

        # Duplicata
        n_duplicada = Nota(
            avaliador=self.avaliador_edicao1,
            projeto=self.projeto1,
            criterio=self.criterio1_ed1,
            nota=Decimal('9.00')
        )
        with self.assertRaises(ValidationError) as cm:
            n_duplicada.save()
        self.assertIn('__all__', cm.exception.message_dict)

    def test_projeto_notafinal_decimal(self):
        self.projeto1.notaFinal_projeto = Decimal('9.75')
        self.projeto1.save()
        self.projeto1.refresh_from_db()
        self.assertEqual(self.projeto1.notaFinal_projeto, Decimal('9.75'))
