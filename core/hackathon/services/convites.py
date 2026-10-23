from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from ..models import ConviteEquipe, ParticipanteEquipe
from ..models.user import tipoUser
from .inscricao import _exigir_inscricao_aberta, _travar_edicao


def url_convite(convite):
    return f"{settings.FRONTEND_URL}/convite/{convite.token}"


def link_ativo(equipe):
    return equipe.convites.filter(ativo=True).first()


def gerar_link(equipe):
    """Cria o link reutilizável da equipe (desativa o anterior, se houver)."""
    with transaction.atomic():
        _exigir_inscricao_aberta(_travar_edicao(equipe.edicao_id))
        equipe.convites.filter(ativo=True).update(ativo=False)
        return ConviteEquipe.objects.create(equipe=equipe)


def revogar_link(equipe):
    with transaction.atomic():
        _exigir_inscricao_aberta(_travar_edicao(equipe.edicao_id))
        equipe.convites.filter(ativo=True).update(ativo=False)


def obter_por_token(token):
    convite = ConviteEquipe.objects.select_related("equipe__edicao", "equipe__criador").filter(token=token).first()
    if convite is None:
        raise NotFound("Convite não encontrado.")
    return convite


def situacao(convite):
    """(valido, motivo) para exibir na tela do convite."""
    equipe = convite.equipe
    if not convite.ativo:
        return False, "Este link de convite foi desativado."
    if equipe.edicao.status != "INSCRICAO":
        return False, "As inscrições desta edição já foram encerradas."
    if equipe.participantes.count() >= equipe.edicao.maximo_participantes:
        return False, "A equipe já está completa."
    return True, ""


def aceitar(usuario, token):
    with transaction.atomic():
        convite = obter_por_token(token)
        equipe = convite.equipe
        edicao = _travar_edicao(equipe.edicao_id)
        _exigir_inscricao_aberta(edicao)
        convite.refresh_from_db()
        valido, motivo = situacao(convite)
        if not valido:
            raise ValidationError({"detail": motivo})
        if usuario.tipoUser != tipoUser.participante:
            raise ValidationError({"detail": "Apenas contas com perfil de Participante podem entrar em equipes."})
        if ParticipanteEquipe.objects.filter(user=usuario, equipe__edicao=edicao).exists():
            raise ValidationError({"detail": "Você já faz parte de uma equipe nesta edição."})
        ParticipanteEquipe.objects.create(user=usuario, equipe=equipe)
        return equipe
