from rest_framework import serializers
from ..models.user import tipoUser


def validate_participante_tipo(user):
    """
    Valida se o usuário possui perfil de PARTICIPANTE.
    Apenas participantes podem fazer parte de equipes.
    """
    if user and getattr(user, 'tipoUser', None) != tipoUser.participante:
        raise serializers.ValidationError(
            "Apenas usuários com perfil de Participante podem fazer parte de uma equipe."
        )
