from rest_framework import serializers
from ..models import User
from ..permissions import is_admin
from ..validations.user_validation import validate_user_tipo
from .imagem import LimpaImagensAntigasMixin

class UserSerializer(LimpaImagensAntigasMixin, serializers.ModelSerializer):
    campos_imagem = ('foto_perfil',)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'first_name', 'last_name',
            'email', 'tipoUser', 'foto_perfil', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'is_active', 'date_joined']

    def validate_tipoUser(self, value):
        request = self.context.get('request')
        request_user = None
        if request:
            request_user = getattr(request, 'user', None) or getattr(request, '_force_auth_user', None)
        validate_user_tipo(value, request_user)
        # Não administradores nunca alteram o próprio tipoUser.
        if (
            self.instance is not None
            and value != self.instance.tipoUser
            and not is_admin(request_user)
        ):
            raise serializers.ValidationError("Você não pode alterar o tipo de usuário.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'tipoUser', 'foto_perfil']
