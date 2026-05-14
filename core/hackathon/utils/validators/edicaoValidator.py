from django.core.exceptions import ValidationError

from django.core.exceptions import ValidationError


def validar_edicao(edicao):
    errors = {}

    if edicao.data_inicio >= edicao.data_fim:
        errors["data_fim"] = \
            "A data final deve ser maior que a inicial."

    if edicao.maximo_participantes < edicao.minimo_participantes:
        errors["maximo_participantes"] = \
            "O máximo deve ser maior ou igual ao mínimo."

    if edicao.maximo_equipes <= 0:
        errors["maximo_equipes"] = \
            "O número máximo de equipes deve ser maior que zero."

    if errors:
        raise ValidationError(errors)