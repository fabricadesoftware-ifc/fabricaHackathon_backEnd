from rest_framework import serializers


def validate_edicao(data):
    errors = {}

    inicio = data.get("data_inicio")
    fim = data.get("data_fim")

    if inicio and fim and fim <= inicio:
        errors["data_fim"] = "A data de fim deve ser maior que a data de início."

    min_p = data.get("minimo_participantes")
    max_p = data.get("maximo_participantes")

    if min_p is not None and max_p is not None:
        if min_p > max_p:
            errors["minimo_participantes"] = (
                "O mínimo deve ser menor ou igual ao máximo."
            )

    max_eq = data.get("maximo_equipes")
    if max_eq is not None and max_eq <= 0:
        errors["maximo_equipes"] = "Deve ser maior que zero."

    if errors:
        raise serializers.ValidationError(errors)

    return data