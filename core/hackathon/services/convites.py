import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from ..models import ConviteEquipe, Equipe, ParticipanteEquipe
from ..models.user import tipoUser
from .inscricao import _exigir_inscricao_aberta, _travar_edicao

logger = logging.getLogger(__name__)


def url_convite(convite):
    return f"{settings.FRONTEND_URL}/convite/{convite.token}"


def enviar_email(convite):
    """Envia o e-mail do convite. Falha de SMTP nunca derruba a requisição: fica registrada em `email_enviado`."""
    equipe = convite.equipe
    criador = equipe.criador.get_full_name().strip() if equipe.criador else ""
    quem = criador or (equipe.criador.email if equipe.criador else "Um participante")
    corpo = (
        f"Olá!\n\n{quem} convidou você para a equipe \"{equipe.nome_equipe}\" na edição "
        f"\"{equipe.edicao.nome}\".\n\n"
        f"Para aceitar, abra o link abaixo (se ainda não tiver conta, crie uma com este e-mail):\n"
        f"{url_convite(convite)}\n\nSe você não esperava este convite, ignore esta mensagem."
    )
    try:
        enviados = send_mail(
            f"Convite para a equipe {equipe.nome_equipe}", corpo, settings.DEFAULT_FROM_EMAIL, [convite.email],
        )
        convite.email_enviado = bool(enviados)
    except Exception:
        logger.exception("Falha ao enviar o e-mail de convite %s.", convite.pk)
        convite.email_enviado = False
    convite.save(update_fields=["email_enviado"])


def enviar_novos(equipe):
    for convite in getattr(equipe, "_novos_convites", []):
        enviar_email(convite)


def _exigir_pendente_da_equipe(equipe, convite_id):
    convite = equipe.convites.filter(pk=convite_id).first()
    if convite is None:
        raise NotFound("Convite não encontrado.")
    return convite


def cancelar_convite(equipe, convite_id):
    with transaction.atomic():
        _exigir_inscricao_aberta(_travar_edicao(equipe.edicao_id))
        convite = _exigir_pendente_da_equipe(equipe, convite_id)
        if convite.status != ConviteEquipe.Status.PENDENTE:
            raise ValidationError({"detail": "Este convite não está mais pendente."})
        convite.status = ConviteEquipe.Status.CANCELADO
        convite.save(update_fields=["status"])


def reenviar_convite(equipe, convite_id):
    with transaction.atomic():
        _exigir_inscricao_aberta(_travar_edicao(equipe.edicao_id))
        convite = _exigir_pendente_da_equipe(equipe, convite_id)
        if convite.status != ConviteEquipe.Status.PENDENTE or convite.eh_link:
            raise ValidationError({"detail": "Só é possível reenviar convites por e-mail pendentes."})
    enviar_email(convite)
    return convite


def gerar_link(equipe):
    """Cria o link reutilizável da equipe (revoga o anterior, se houver)."""
    with transaction.atomic():
        _exigir_inscricao_aberta(_travar_edicao(equipe.edicao_id))
        equipe.convites.filter(email="", status=ConviteEquipe.Status.PENDENTE).update(
            status=ConviteEquipe.Status.CANCELADO
        )
        return ConviteEquipe.objects.create(equipe=equipe)


def revogar_link(equipe):
    with transaction.atomic():
        _exigir_inscricao_aberta(_travar_edicao(equipe.edicao_id))
        equipe.convites.filter(email="", status=ConviteEquipe.Status.PENDENTE).update(
            status=ConviteEquipe.Status.CANCELADO
        )


def link_ativo(equipe):
    return equipe.convites.filter(email="", status=ConviteEquipe.Status.PENDENTE).first()


def obter_por_token(token):
    convite = ConviteEquipe.objects.select_related("equipe__edicao", "equipe__criador").filter(token=token).first()
    if convite is None:
        raise NotFound("Convite não encontrado.")
    return convite


def situacao(convite):
    """(valido, motivo) para exibir na tela do convite."""
    edicao = convite.equipe.edicao
    if convite.status == ConviteEquipe.Status.CANCELADO:
        return False, "Este convite foi cancelado."
    if convite.status == ConviteEquipe.Status.ACEITO:
        return False, "Este convite já foi usado."
    if edicao.status != "INSCRICAO":
        return False, "As inscrições desta edição já foram encerradas."
    return True, ""


def aceitar(usuario, token):
    with transaction.atomic():
        convite = obter_por_token(token)
        equipe = convite.equipe
        edicao = _travar_edicao(equipe.edicao_id)
        convite = ConviteEquipe.objects.select_for_update().get(pk=convite.pk)
        _exigir_inscricao_aberta(edicao)
        if convite.status != ConviteEquipe.Status.PENDENTE:
            raise ValidationError({"detail": situacao(convite)[1]})
        if usuario.tipoUser != tipoUser.participante:
            raise ValidationError({"detail": "Apenas contas com perfil de Participante podem entrar em equipes."})
        if ParticipanteEquipe.objects.filter(user=usuario, equipe__edicao=edicao).exists():
            raise ValidationError({"detail": "Você já faz parte de uma equipe nesta edição."})

        membros = equipe.participantes.count()
        outros_convites = equipe.convites.filter(status="PENDENTE").exclude(email="").exclude(pk=convite.pk).count()
        _validar_total_vaga(edicao, membros + outros_convites + 1)

        ParticipanteEquipe.objects.create(user=usuario, equipe=equipe)
        if not convite.eh_link:
            convite.status = ConviteEquipe.Status.ACEITO
            convite.aceito_em = timezone.now()
            convite.aceito_por = usuario
            convite.save(update_fields=["status", "aceito_em", "aceito_por"])
        return equipe


def _validar_total_vaga(edicao, total):
    if total > edicao.maximo_participantes:
        raise ValidationError({"detail": "A equipe já está completa."})
