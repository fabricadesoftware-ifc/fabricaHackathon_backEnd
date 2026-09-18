from datetime import date, timedelta
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import serializers

from .models import (
    User,
    Equipe,
    Edicao,
    Tema,
    Projeto,
    TipoEdicao,
    ParticipanteEquipe
)
from .models.user import tipoUser
from .serializers import (
    UserSerializer,
    ParticipanteEquipeSerializer
)
from .views import (
    UserViewSet,
    ParticipanteEquipeViewSet
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
