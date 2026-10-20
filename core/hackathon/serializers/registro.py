from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from ..models import SolicitacaoPerfil, User
from ..models.user import tipoUser


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    username = serializers.CharField(required=False, max_length=150)
    perfil_solicitado = serializers.ChoiceField(
        choices=SolicitacaoPerfil.PERFIS_SOLICITAVEIS, required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password', 'perfil_solicitado']
        read_only_fields = ['id']
        extra_kwargs = {'email': {'required': True}}

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Já existe uma conta cadastrada com este e-mail.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Este nome de usuário já está em uso.")
        return value

    def validate(self, attrs):
        attrs.setdefault('username', attrs['email'])
        if User.objects.filter(username__iexact=attrs['username']).exists():
            raise serializers.ValidationError({'username': "Este nome de usuário já está em uso."})
        candidato = User(
            username=attrs['username'], email=attrs['email'],
            first_name=attrs.get('first_name', ''), last_name=attrs.get('last_name', ''),
        )
        try:
            validate_password(attrs['password'], candidato)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(getattr(exc, 'messages', [str(exc)]))})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        perfil = validated_data.pop('perfil_solicitado', None)
        password = validated_data.pop('password')
        user = User(**validated_data, tipoUser=tipoUser.participante)
        user.set_password(password)
        user.save()
        if perfil:
            SolicitacaoPerfil.objects.create(usuario=user, perfil_solicitado=perfil)
        return user


class SolicitacaoPerfilSerializer(serializers.ModelSerializer):
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    usuario_nome = serializers.SerializerMethodField()
    decidida_por_email = serializers.EmailField(source='decidida_por.email', read_only=True, default=None)

    class Meta:
        model = SolicitacaoPerfil
        fields = [
            'id', 'usuario', 'usuario_email', 'usuario_nome', 'perfil_solicitado', 'status',
            'criada_em', 'decidida_em', 'decidida_por', 'decidida_por_email',
        ]
        read_only_fields = fields

    def get_usuario_nome(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username
