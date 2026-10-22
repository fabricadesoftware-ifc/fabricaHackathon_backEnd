from rest_framework.exceptions import ValidationError


def int_param(request, name):
    """Lê um filtro inteiro da query string; valor inválido vira 400 (nunca 500)."""
    raw = request.query_params.get(name)
    if raw in (None, ""):
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError({name: "Informe um número inteiro."})
    if not -2147483648 <= value <= 2147483647:
        raise ValidationError({name: "Valor fora do intervalo permitido."})
    return value
