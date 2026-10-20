from decimal import Decimal, ROUND_HALF_UP


def recalcular_nota_final(projeto):
    """
    Nota final do projeto = média das médias de cada avaliador vinculado à edição.
    O projeto só recebe nota quando TODOS os avaliadores vinculados avaliaram TODOS
    os critérios da edição; caso contrário a nota fica nula.
    """
    from ..models import AvaliadorEdicao, Criterio, Nota, Projeto

    total_criterios = Criterio.objects.filter(edicao_id=projeto.edicao_id).count()
    avaliadores = list(AvaliadorEdicao.objects.filter(edicao_id=projeto.edicao_id).values_list('id', flat=True))
    nova = None
    if total_criterios and avaliadores:
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
            nova = (sum(medias) / len(medias)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    Projeto.objects.filter(pk=projeto.pk).update(notaFinal_projeto=nova)
    projeto.notaFinal_projeto = nova
    return nova
