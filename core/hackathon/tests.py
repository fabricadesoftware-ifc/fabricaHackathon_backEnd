from django.test import TestCase
from django.contrib.auth.models import User as AuthUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import serializers

from .models import User
from .models.user import tipoUser
from .serializers import UserSerializer
from .views import UserViewSet


class UserTipoValidationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        # Usuário Auth comum (participante)
        self.auth_participante = AuthUser.objects.create_user(
            username='participante',
            email='participante@test.com',
            password='password123'
        )
        self.user_participante = User.objects.create(
            auth_user=self.auth_participante,
            nome_user='Participante Teste',
            email_user='participante@test.com',
            tipoUser=tipoUser.participante
        )

        # Usuário Auth Admin (staff / hackathon admin)
        self.auth_admin = AuthUser.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password123'
        )
        self.user_admin = User.objects.create(
            auth_user=self.auth_admin,
            nome_user='Admin Teste',
            email_user='admin@test.com',
            tipoUser=tipoUser.admin
        )

        # Novo auth user que será associado no teste
        self.novo_auth_user = AuthUser.objects.create_user(
            username='novouser',
            email='novouser@test.com',
            password='password123'
        )

    def test_anonymous_cannot_set_admin(self):
        data = {
            'auth_user_id': self.novo_auth_user.id,
            'nome_user': 'Novo User',
            'email_user': 'novouser@test.com',
            'tipoUser': tipoUser.admin
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipoUser', serializer.errors)

    def test_anonymous_cannot_set_avaliador(self):
        data = {
            'auth_user_id': self.novo_auth_user.id,
            'nome_user': 'Novo User',
            'email_user': 'novouser@test.com',
            'tipoUser': tipoUser.avaliador
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipoUser', serializer.errors)

    def test_participante_cannot_set_admin(self):
        request = self.factory.post('/api/users/')
        force_authenticate(request, user=self.auth_participante)

        data = {
            'auth_user_id': self.novo_auth_user.id,
            'nome_user': 'Novo User',
            'email_user': 'novouser@test.com',
            'tipoUser': tipoUser.admin
        }
        serializer = UserSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipoUser', serializer.errors)

    def test_participante_cannot_set_avaliador(self):
        request = self.factory.post('/api/users/')
        force_authenticate(request, user=self.auth_participante)

        data = {
            'auth_user_id': self.novo_auth_user.id,
            'nome_user': 'Novo User',
            'email_user': 'novouser@test.com',
            'tipoUser': tipoUser.avaliador
        }
        serializer = UserSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipoUser', serializer.errors)

    def test_participante_can_set_participante(self):
        request = self.factory.post('/api/users/')
        force_authenticate(request, user=self.auth_participante)

        data = {
            'auth_user_id': self.novo_auth_user.id,
            'nome_user': 'Novo User',
            'email_user': 'novouser@test.com',
            'tipoUser': tipoUser.participante
        }
        serializer = UserSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_admin_can_set_avaliador_and_admin(self):
        request = self.factory.post('/api/users/')
        force_authenticate(request, user=self.auth_admin)

        # Criando como avaliador
        data_avaliador = {
            'auth_user_id': self.novo_auth_user.id,
            'nome_user': 'Novo Avaliador',
            'email_user': 'novouser@test.com',
            'tipoUser': tipoUser.avaliador
        }
        serializer_avaliador = UserSerializer(data=data_avaliador, context={'request': request})
        self.assertTrue(serializer_avaliador.is_valid(), serializer_avaliador.errors)

        # Criando como admin
        data_admin = {
            'auth_user_id': self.novo_auth_user.id,
            'nome_user': 'Novo Admin',
            'email_user': 'novouser@test.com',
            'tipoUser': tipoUser.admin
        }
        serializer_admin = UserSerializer(data=data_admin, context={'request': request})
        self.assertTrue(serializer_admin.is_valid(), serializer_admin.errors)

    def test_api_viewset_blocks_unauthorized_role_assignment(self):
        view = UserViewSet.as_view({'post': 'create'})
        request = self.factory.post('/api/users/', {
            'auth_user_id': self.novo_auth_user.id,
            'nome_user': 'Hacker',
            'email_user': 'hacker@test.com',
            'tipoUser': tipoUser.admin
        }, format='json')
        force_authenticate(request, user=self.auth_participante)

        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('tipoUser', response.data)
