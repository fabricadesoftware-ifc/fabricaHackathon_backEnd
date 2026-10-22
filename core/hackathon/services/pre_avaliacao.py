import ipaddress
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlparse

from django.utils import timezone

# Mínimo de caracteres das respostas dissertativas (conta ponto só por existir, sem avaliar qualidade).
MIN_CARACTERES = 30
# Cada seção vale 2 pontos; 5 seções = 10 pontos (a nota da pré-avaliação vai de 0 a 10).
PONTOS_SECAO = Decimal("2.00")
PESO_AVALIADORES = Decimal("0.90")
PESO_PRE_AVALIACAO = Decimal("0.10")
METADE = Decimal("0.5")


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


def _texto_ok(valor):
    return len((valor or "").strip()) >= MIN_CARACTERES


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


def _item(id_, descricao, maximo, fracao, motivo):
    return {
        "id": id_, "descricao": descricao, "maximo": str(maximo),
        "pontos": str((maximo * fracao).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "motivo": motivo,
    }


def pontuar(pre, membros_ids):
    """
    Pontuação automática (0–10) do formulário:
      - respondeu/entregou = 100% dos pontos do item;
      - entregou mas está local (aplicação ou banco) = 50%;
      - em branco, ou RFs/RNFs não entregue = 0% (só aquele item).
    Itens da mesma seção dividem os 2 pontos da seção igualmente.
    """
    secoes = []

    def secao(id_, titulo, itens):
        pontos = sum((Decimal(i["pontos"]) for i in itens), Decimal("0"))
        secoes.append({
            "id": id_, "titulo": titulo, "maximo": str(PONTOS_SECAO),
            "pontos": str(pontos.quantize(Decimal("0.01"))), "itens": itens,
        })

    # Seção 1: equipe e organização (2 itens de 1,0)
    areas = {}
    for entrada in pre.responsabilidades or []:
        if isinstance(entrada, dict) and str(entrada.get("area", "")).strip():
            areas[entrada.get("user")] = True
    completo = bool(membros_ids) and all(m in areas for m in membros_ids)
    um = Decimal("1.00")
    secao(1, "Equipe e organização", [
        _item("responsabilidades", "Responsável/área de cada integrante", um,
              Decimal(1) if completo else Decimal(0),
              "ok" if completo else "faltam integrantes sem área definida"),
        _item("organizacao", "Como a equipe se organizou", um,
              Decimal(1) if pre.organizacao_metodo else Decimal(0),
              "ok" if pre.organizacao_metodo else "não respondido"),
    ])

    # Seção 2: entendimento do problema (4 itens de 0,5)
    meio = Decimal("0.50")
    textos = [
        ("problema_entendido", "Problema que entenderam", pre.problema_entendido),
        ("problema_explicacao", "Explicação para alguém de fora", pre.problema_explicacao),
        ("maior_dificuldade", "Maior dificuldade enfrentada", pre.maior_dificuldade),
        ("proximos_passos", "Próximos passos", pre.proximos_passos),
    ]
    secao(2, "Entendimento do problema", [
        _item(i, d, meio, Decimal(1) if _texto_ok(v) else Decimal(0),
              "ok" if _texto_ok(v) else f"resposta com menos de {MIN_CARACTERES} caracteres")
        for i, d, v in textos
    ])

    # Seção 3: arquivos de arquitetura (2 itens de 1,0)
    tem_rfs = bool(pre.arquivo_rfs_rnfs)
    tem_arq = bool(pre.arquitetura_arquivo) or bool((pre.arquitetura_link or "").strip())
    secao(3, "Arquivos de arquitetura", [
        _item("rfs_rnfs", "Arquivo de RFs e RNFs", um, Decimal(1) if tem_rfs else Decimal(0),
              "ok" if tem_rfs else "arquivo não entregue"),
        _item("arquitetura", "Arquivos de arquitetura (requisitos e BD)", um,
              Decimal(1) if tem_arq else Decimal(0), "ok" if tem_arq else "não entregue"),
    ])

    # Seção 4: aplicação hospedada
    plat = pre.hospedagem_plataforma
    link = (pre.hospedagem_link or "").strip()
    if not plat:
        fr, motivo = Decimal(0), "não respondido"
    elif plat == "LOCAL" or link_local(link):
        fr, motivo = METADE, "aplicação local (50%)"
    elif not link:
        fr, motivo = Decimal(0), "link da aplicação não informado"
    else:
        fr, motivo = Decimal(1), "ok"
    secao(4, "Aplicação hospedada", [
        _item("hospedagem", "Onde hospedou e link", um, fr, motivo),
        _item("hospedagem_justificativa", "Por que hospedou aí", um,
              Decimal(1) if _texto_ok(pre.hospedagem_justificativa) else Decimal(0),
              "ok" if _texto_ok(pre.hospedagem_justificativa) else f"menos de {MIN_CARACTERES} caracteres"),
    ])

    # Seção 5: banco de dados
    if not pre.banco_plataforma:
        fb, mb = Decimal(0), "não respondido"
    elif pre.banco_plataforma == "LOCAL":
        fb, mb = METADE, "banco local (50%)"
    else:
        fb, mb = Decimal(1), "ok"
    secao(5, "Banco de dados", [
        _item("banco", "Onde foi feito o deploy do banco", um, fb, mb),
        _item("banco_justificativa", "Por que essa escolha", um,
              Decimal(1) if _texto_ok(pre.banco_justificativa) else Decimal(0),
              "ok" if _texto_ok(pre.banco_justificativa) else f"menos de {MIN_CARACTERES} caracteres"),
    ])

    total = sum((Decimal(s["pontos"]) for s in secoes), Decimal("0")).quantize(Decimal("0.01"))
    return total, {"secoes": secoes, "total": str(total)}


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
