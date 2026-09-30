from rest_framework import serializers


def validate_nota_edicao(avaliador, projeto, criterio):
    """
    Valida se avaliador, projeto e critério pertencem à mesma edição.
    """
    if avaliador and projeto:
        avaliador_edicao_id = getattr(avaliador, 'edicao_id', None) or (avaliador.edicao.id if hasattr(avaliador, 'edicao') else None)
        projeto_edicao_id = getattr(projeto, 'edicao_id', None) or (projeto.edicao.id if hasattr(projeto, 'edicao') else None)
        if avaliador_edicao_id != projeto_edicao_id:
            raise serializers.ValidationError(
                {"avaliador": "O avaliador não pertence à mesma edição do projeto avaliado."}
            )

    if criterio and projeto:
        criterio_edicao_id = getattr(criterio, 'edicao_id', None) or (criterio.edicao.id if hasattr(criterio, 'edicao') else None)
        projeto_edicao_id = getattr(projeto, 'edicao_id', None) or (projeto.edicao.id if hasattr(projeto, 'edicao') else None)
        if criterio_edicao_id != projeto_edicao_id:
            raise serializers.ValidationError(
                {"criterio": "O critério não pertence à mesma edição do projeto avaliado."}
            )


def validate_nota_unica(avaliador, projeto, criterio, instance=None):
    """
    Valida se já existe uma nota registrada para o mesmo avaliador, projeto e critério.
    """
    from ..models import Nota

    if not avaliador or not projeto or not criterio:
        return

    avaliador_id = getattr(avaliador, 'pk', avaliador)
    projeto_id = getattr(projeto, 'pk', projeto)
    criterio_id = getattr(criterio, 'pk', criterio)

    qs = Nota.objects.filter(
        avaliador_id=avaliador_id,
        projeto_id=projeto_id,
        criterio_id=criterio_id
    )
    if instance and instance.pk:
        qs = qs.exclude(pk=instance.pk)

    if qs.exists():
        raise serializers.ValidationError(
            {"non_field_errors": ["Este critério já foi avaliado por este avaliador para este projeto."]}
        )
