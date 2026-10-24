import ipaddress
from decimal import Decimal
from urllib.parse import urlparse

from django.utils import timezone

PESO_AVALIADORES = Decimal("0.90")
PESO_PRE_AVALIACAO = Decimal("0.10")


def link_local(url):
    """True se a URL aponta para localhost, 127.x, rede interna ou nomes internos."""
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".lan", ".home")):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return "." not in host  # nome sem domínio (ex.: "meuservidor") é rede interna
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified


def _aberta(edicao, agora=None):
    """Retorna (aberta, motivo)."""
    agora = agora or timezone.now()
    if edicao.status != "EM_ANDAMENTO":
        return False, "A pré-avaliação só pode ser preenchida enquanto a edição está em andamento."
    if not edicao.pre_avaliacao_liberada:
        return False, "A pré-avaliação ainda não foi liberada pela organização."
    if edicao.prazo_pre_avaliacao and agora > edicao.prazo_pre_avaliacao:
        return False, "O prazo da pré-avaliação foi encerrado."
    return True, ""


def pre_avaliacao_aberta(edicao, agora=None):
    return _aberta(edicao, agora)[0]


def motivo_fechada(edicao, agora=None):
    return _aberta(edicao, agora)[1]


NOTA_RESPONDEU = Decimal("10.00")


def respondeu(pre):
    """True se a equipe registrou ao menos uma resposta/arquivo na pré-avaliação."""
    campos = [
        pre.organizacao_metodo, pre.problema_entendido, pre.problema_explicacao, pre.maior_dificuldade,
        pre.proximos_passos, pre.arquitetura_link, pre.hospedagem_plataforma, pre.hospedagem_link,
        pre.hospedagem_justificativa, pre.banco_plataforma, pre.banco_justificativa,
    ]
    if any((c or "").strip() for c in campos):
        return True
    if any(isinstance(e, dict) and str(e.get("area", "")).strip() for e in (pre.responsabilidades or [])):
        return True
    return bool(pre.arquivo_rfs_rnfs or pre.arquitetura_arquivo)


def pontuar(pre, membros_ids=None):
    """Sem pesos internos: respondeu a pré-avaliação = 10; não respondeu = 0."""
    nota = NOTA_RESPONDEU if respondeu(pre) else Decimal("0.00")
    return nota, {"total": str(nota), "respondeu": nota > 0}


def _publicar_link_hospedagem(pre):
    """O link de hospedagem informado na pré-avaliação vira o link público do projeto (se não for local)."""
    link = (pre.hospedagem_link or "").strip()
    projeto = pre.projeto
    if link and not link_local(link) and projeto.link_deploy_projeto != link:
        projeto.link_deploy_projeto = link
        projeto.save(update_fields=["link_deploy_projeto"])


def salvar_com_pontuacao(pre):
    """Recalcula a nota da pré-avaliação, grava e atualiza a nota final do projeto."""
    from .nota_final import recalcular_nota_final

    membros = list(pre.projeto.equipes.participantes.values_list("user_id", flat=True))
    pre.nota, pre.detalhe_pontuacao = pontuar(pre, membros)
    pre.save()
    _publicar_link_hospedagem(pre)
    recalcular_nota_final(pre.projeto)
    return pre
