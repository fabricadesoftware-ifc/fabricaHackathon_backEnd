from rest_framework import serializers
from ..models.user import tipoUser
from .user_validation import validate_user_tipo_perfil


def validate_avaliador_tipo(user):
    """
    Valida se o usuário possui perfil de AVALIADOR.
    Apenas avaliadores podem ser vinculados a edições.
    """
    validate_user_tipo_perfil(
        user,
        tipoUser.avaliador,
        "Apenas usuários com perfil de Avaliador podem ser vinculados a uma edição."
    )


def validate_avaliador_edicao_unica(user, edicao, instance=None):
    """
    Valida se o usuário já está vinculado como avaliador nesta edição.
    """
    from ..models import AvaliadorEdicao

    if not user or not edicao:
        return

    qs = AvaliadorEdicao.objects.filter(user=user, edicao=edicao)
    if instance and instance.pk:
        qs = qs.exclude(pk=instance.pk)

    if qs.exists():
        raise serializers.ValidationError(
            {"user": f"O usuário '{user.username}' já está vinculado como avaliador nesta edição."}
        )
