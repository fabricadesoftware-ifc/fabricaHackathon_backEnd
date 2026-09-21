from rest_framework import serializers
from ..models.user import tipoUser


def validate_user_tipo(tipo_solicitado, request_user=None):
    """
    Valida a atribuição de tipoUser.
    Papéis restritos (ADMIN e AVALIADOR) só podem ser concedidos por
    um administrador autenticado.
    """
    papeis_restritos = [tipoUser.admin, tipoUser.avaliador]

    if tipo_solicitado in papeis_restritos:
        if not request_user or not request_user.is_authenticated:
            raise serializers.ValidationError(
                "Apenas administradores podem atribuir perfis de Avaliador ou Administrador."
            )

        is_admin = (
            request_user.is_staff
            or request_user.is_superuser
            or getattr(request_user, "tipoUser", None) == tipoUser.admin
            or getattr(getattr(request_user, "hackathon_user", None), "tipoUser", None) == tipoUser.admin
        )

        if not is_admin:
            raise serializers.ValidationError(
                "Você não tem permissão para cadastrar ou alterar usuários para este perfil."
            )


def validate_user_tipo_perfil(user, tipo_esperado, mensagem=None):
    """
    Valida se o usuário possui o tipoUser esperado.
    Evita duplicação de lógica entre diferentes entidades (Participante, Avaliador, Admin).
    """
    if user and getattr(user, 'tipoUser', None) != tipo_esperado:
        raise serializers.ValidationError(
            mensagem or f"Apenas usuários com perfil de {tipo_esperado} podem realizar esta ação."
        )
