from rest_framework import serializers
from django.contrib.auth.models import User as AuthUser
from ..models import User
from ..validations.user_validation import validate_user_tipo

class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserSerializer(serializers.ModelSerializer):
    auth_user = AuthUserSerializer(read_only=True)
    auth_user_id = serializers.PrimaryKeyRelatedField(
        queryset=AuthUser.objects.all(), source='auth_user', write_only=True
    )

    class Meta:
        model = User
        fields = ['id', 'auth_user', 'auth_user_id', 'nome_user', 'email_user', 'tipoUser']

    def validate_tipoUser(self, value):
        request = self.context.get('request')
        request_user = None
        if request:
            request_user = getattr(request, 'user', None) or getattr(request, '_force_auth_user', None)
        validate_user_tipo(value, request_user)
        return value

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nome_user', 'tipoUser']
