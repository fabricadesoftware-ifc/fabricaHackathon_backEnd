from rest_framework import serializers
from ..models import User
from ..validations.user_validation import validate_user_tipo

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'nome_user', 'email_user', 'tipoUser', 'is_active', 'date_joined']
        read_only_fields = ['id', 'is_active', 'date_joined']

    def validate_tipoUser(self, value):
        request = self.context.get('request')
        request_user = None
        if request:
            request_user = getattr(request, 'user', None) or getattr(request, '_force_auth_user', None)
        validate_user_tipo(value, request_user)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if 'email_user' in validated_data and not validated_data.get('email'):
            validated_data['email'] = validated_data['email_user']
        if 'nome_user' in validated_data and not validated_data.get('first_name'):
            validated_data['first_name'] = validated_data['nome_user']

        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'nome_user', 'email_user', 'tipoUser']
