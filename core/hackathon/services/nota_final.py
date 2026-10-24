from decimal import Decimal, ROUND_HALF_UP


def recalcular_nota_final(projeto):
    """
    Nota final do projeto = 90% da média das médias de cada avaliador vinculado à edição
    + 10% da nota da pré-avaliação (0 se a equipe não respondeu).
    O projeto só recebe nota quando TODOS os avaliadores vinculados avaliaram TODOS
    os critérios da edição; caso contrário a nota fica nula.
    """
    from ..models import AvaliadorEdicao, Criterio, Nota, PreAvaliacao, Projeto
    from .pre_avaliacao import PESO_AVALIADORES, PESO_PRE_AVALIACAO

    equipe = getattr(projeto, 'equipes', None)
    fora = bool(equipe is not None and equipe.organizadora)  # equipe da Fábrica não é avaliada
    total_criterios = Criterio.objects.filter(edicao_id=projeto.edicao_id).count()
    avaliadores = list(AvaliadorEdicao.objects.filter(edicao_id=projeto.edicao_id).values_list('id', flat=True))
    nova = None
    if total_criterios and avaliadores and not fora:
        medias = []
        for avaliador_id in avaliadores:
            valores = list(
                Nota.objects.filter(projeto_id=projeto.pk, avaliador_id=avaliador_id).values_list('nota', flat=True)
            )
            if len(valores) < total_criterios:
                medias = None
                break
            medias.append(sum(valores) / len(valores))
        if medias:
            media_avaliadores = sum(medias) / len(medias)
            pre = PreAvaliacao.objects.filter(projeto_id=projeto.pk).values_list('nota', flat=True).first()
            nota_pre = Decimal(pre) if pre is not None else Decimal('0')
            nova = (media_avaliadores * PESO_AVALIADORES + nota_pre * PESO_PRE_AVALIACAO).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
    Projeto.objects.filter(pk=projeto.pk).update(notaFinal_projeto=nova)
    projeto.notaFinal_projeto = nova
    return nova
