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


def validate_participante_edicao_unica(user, equipe, instance=None):
    """
    Valida se o usuário já participa de outra equipe na mesma edição.
    """
    from ..models import ParticipanteEquipe

    if not user or not equipe:
        return

    qs = ParticipanteEquipe.objects.filter(
        user=user,
        equipe__edicao=equipe.edicao
    )
    if instance and instance.pk:
        qs = qs.exclude(pk=instance.pk)

    equipe_existente = qs.select_related('equipe').first()
    if equipe_existente:
        raise serializers.ValidationError(
            {"user": f"O usuário '{user.username}' já faz parte da equipe '{equipe_existente.equipe.nome_equipe}' nesta mesma edição."}
        )
