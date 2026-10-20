from rest_framework import serializers


def validate_edicao(data):
    errors = {}

    inicio = data.get("data_inicio")
    fim = data.get("data_fim")

    if inicio is not None and fim is not None:
        if fim <= inicio:
            errors["data_fim"] = "A data de fim deve ser maior que a data de início."

    min_p = data.get("minimo_participantes")
    max_p = data.get("maximo_participantes")

    if min_p is not None and max_p is not None:
        if min_p > max_p:
            errors["minimo_participantes"] = (
                "O mínimo deve ser menor ou igual ao máximo."
            )

    max_eq = data.get("maximo_equipes")
    
    if max_eq is not None:
        if max_eq <= 0:
            errors["maximo_equipes"] = "Deve ser maior que zero."

    if errors:
        raise serializers.ValidationError(errors)

    return data


ORDEM_STATUS = ["INSCRICAO", "EM_ANDAMENTO", "AVALIACAO", "FINALIZADO"]


def validate_transicao_status(instance, data):
    """
    O status só avança, um passo por vez:
    INSCRICAO → EM_ANDAMENTO → AVALIACAO → FINALIZADO. Vale para qualquer perfil.
    """
    novo = data.get("status")
    if novo is None:
        return
    atual = instance.status if instance is not None else "INSCRICAO"
    if novo == atual:
        return
    if instance is None:
        raise serializers.ValidationError(
            {"status": "Uma edição nova deve começar com o status INSCRICAO."}
        )
    indice_atual = ORDEM_STATUS.index(atual)
    if ORDEM_STATUS.index(novo) != indice_atual + 1:
        if indice_atual + 1 < len(ORDEM_STATUS):
            msg = "Transição inválida: de %s só é possível avançar para %s." % (
                atual, ORDEM_STATUS[indice_atual + 1]
            )
        else:
            msg = "A edição está finalizada e não pode mudar de status."
        raise serializers.ValidationError({"status": msg})


def validate_limites_com_instancia(instance, data):
    """Em atualização parcial, confere min/max e maximo_equipes contra os valores já salvos."""
    if instance is None:
        return
    errors = {}
    min_p = data.get("minimo_participantes", instance.minimo_participantes)
    max_p = data.get("maximo_participantes", instance.maximo_participantes)
    if min_p > max_p:
        errors["minimo_participantes"] = "O mínimo deve ser menor ou igual ao máximo."
    max_eq = data.get("maximo_equipes")
    if max_eq is not None and max_eq < instance.equipes.count():
        errors["maximo_equipes"] = (
            "Já existem %d equipes inscritas; o limite não pode ser menor que isso." % instance.equipes.count()
        )
    if errors:
        raise serializers.ValidationError(errors)