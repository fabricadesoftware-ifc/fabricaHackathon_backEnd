from django.db import transaction
from django.db.models import ProtectedError
from rest_framework.exceptions import ValidationError

from ..models import ConviteEquipe, Edicao, Equipe, ParticipanteEquipe, Projeto, User
from ..models.user import tipoUser


def _travar_edicao(edicao_id):
    """Serializa inscrições/alterações de equipe da mesma edição (select_for_update)."""
    return Edicao.objects.select_for_update().get(pk=edicao_id)


def _exigir_inscricao_aberta(edicao):
    if edicao.status != 'INSCRICAO':
        raise ValidationError({'edicao': 'As inscrições desta edição não estão abertas.'})


def _exigir_projeto_editavel(edicao):
    """Dados do projeto (descrição, tema, link, logo) seguem editáveis também com a edição em andamento."""
    if edicao.status not in ('INSCRICAO', 'EM_ANDAMENTO'):
        raise ValidationError({'edicao': 'O projeto só pode ser alterado com a edição em inscrições ou em andamento.'})


def exigir_projeto_editavel(equipe):
    """Garante (com a edição travada) que o projeto da equipe ainda pode ser alterado."""
    with transaction.atomic():
        _exigir_projeto_editavel(_travar_edicao(equipe.edicao_id))


def exigir_inscricao_aberta(equipe):
    """Garante (com a edição travada) que a edição da equipe ainda está em INSCRICAO."""
    with transaction.atomic():
        _exigir_inscricao_aberta(_travar_edicao(equipe.edicao_id))


def _resolver_membros(edicao, emails, ignorar_equipe=None, ignorar_usuarios=(), emails_ja_convidados=()):
    """
    Separa e-mails em usuários já cadastrados (entram direto) e e-mails sem conta (viram convite),
    validando cada regra com mensagens por e-mail. Devolve (usuarios, emails_para_convidar).
    """
    erros = []
    vistos = set()
    usuarios = []
    convidar = []
    for bruto in emails:
        email = bruto.strip().lower()
        if email in vistos:
            erros.append(f"O e-mail {email} foi informado mais de uma vez.")
            continue
        vistos.add(email)
        usuario = User.objects.filter(email__iexact=email).first()
        if usuario is None:
            if email in emails_ja_convidados:
                erros.append(f"O e-mail {email} já foi convidado para esta equipe.")
            else:
                convidar.append(email)
            continue
        if usuario.pk in ignorar_usuarios:
            erros.append(f"O e-mail {email} já pertence a esta equipe.")
            continue
        if usuario.tipoUser != tipoUser.participante:
            erros.append(f"O usuário {email} não tem perfil de Participante.")
            continue
        outra = ParticipanteEquipe.objects.filter(user=usuario, equipe__edicao=edicao)
        if ignorar_equipe is not None:
            outra = outra.exclude(equipe=ignorar_equipe)
        existente = outra.select_related('equipe').first()
        if existente:
            erros.append(f"O usuário {email} já faz parte da equipe '{existente.equipe.nome_equipe}' nesta edição.")
            continue
        usuarios.append(usuario)
    if erros:
        raise ValidationError({'membros': erros})
    return usuarios, convidar


def _validar_total(edicao, total):
    """Máximo vale desde a inscrição (membros + convites por e-mail pendentes). O mínimo vale ao fechar as inscrições."""
    if total > edicao.maximo_participantes:
        raise ValidationError({
            'membros': f"A equipe pode ter no máximo {edicao.maximo_participantes} participantes (contando você e "
                       f"os convites enviados); foram informados {total}."
        })


def _criar_convites(equipe, emails):
    novos = [ConviteEquipe.objects.create(equipe=equipe, email=e) for e in emails]
    equipe._novos_convites = getattr(equipe, '_novos_convites', []) + novos


def criar_inscricao(criador, dados):
    """Cria Equipe + Projeto + ParticipanteEquipe de forma atômica. Qualquer erro desfaz tudo."""
    with transaction.atomic():
        edicao = _travar_edicao(dados['edicao'].pk)
        _exigir_inscricao_aberta(edicao)

        if edicao.equipes.count() >= edicao.maximo_equipes:
            raise ValidationError({'edicao': f"A edição já atingiu o limite de {edicao.maximo_equipes} equipes."})

        tema = dados.get('tema')
        if tema is not None and tema.edicao_id != edicao.pk:
            raise ValidationError({'tema': 'O tema não pertence à edição informada.'})

        if ParticipanteEquipe.objects.filter(user=criador, equipe__edicao=edicao).exists():
            raise ValidationError({'edicao': 'Você já faz parte de uma equipe nesta edição.'})

        if Equipe.objects.filter(edicao=edicao, nome_equipe__iexact=dados['nome_equipe']).exists():
            raise ValidationError({'nome_equipe': 'Já existe uma equipe com este nome nesta edição.'})

        emails = dados.get('membros', [])
        if any(e.strip().lower() == criador.email.lower() for e in emails):
            raise ValidationError({'membros': 'Não inclua o seu próprio e-mail: você já é membro da equipe.'})
        membros, convidar = _resolver_membros(edicao, emails)
        _validar_total(edicao, len(membros) + len(convidar) + 1)

        projeto = Projeto.objects.create(edicao=edicao, **dados['projeto'])
        equipe = Equipe.objects.create(
            nome_equipe=dados['nome_equipe'], edicao=edicao, tema=tema, projeto=projeto, criador=criador,
        )
        for usuario in [criador, *membros]:
            ParticipanteEquipe.objects.create(user=usuario, equipe=equipe)
        _criar_convites(equipe, convidar)
        return equipe


def atualizar_equipe(equipe, dados):
    with transaction.atomic():
        edicao = _travar_edicao(equipe.edicao_id)
        _exigir_projeto_editavel(edicao)
        if 'nome_equipe' in dados:
            # O nome da equipe só muda enquanto as inscrições estão abertas.
            _exigir_inscricao_aberta(edicao)
            if Equipe.objects.filter(edicao=edicao, nome_equipe__iexact=dados['nome_equipe']).exclude(
                pk=equipe.pk
            ).exists():
                raise ValidationError({'nome_equipe': 'Já existe uma equipe com este nome nesta edição.'})
            equipe.nome_equipe = dados['nome_equipe']
        if 'tema' in dados:
            if dados['tema'] is not None and dados['tema'].edicao_id != edicao.pk:
                raise ValidationError({'tema': 'O tema não pertence à edição informada.'})
            equipe.tema = dados['tema']
        equipe.save()
        projeto = equipe.projeto
        for campo, valor in dados.get('projeto', {}).items():
            setattr(projeto, campo, valor)
        projeto.save()
        return equipe


def adicionar_membros(equipe, emails):
    with transaction.atomic():
        edicao = _travar_edicao(equipe.edicao_id)
        _exigir_inscricao_aberta(edicao)
        atuais = list(equipe.participantes.values_list('user_id', flat=True))
        pendentes = list(equipe.convites.filter(status='PENDENTE').exclude(email='').values_list('email', flat=True))
        novos, convidar = _resolver_membros(
            edicao, emails, ignorar_equipe=equipe, ignorar_usuarios=atuais,
            emails_ja_convidados={e.lower() for e in pendentes},
        )
        _validar_total(edicao, len(atuais) + len(pendentes) + len(novos) + len(convidar))
        for usuario in novos:
            ParticipanteEquipe.objects.create(user=usuario, equipe=equipe)
        _criar_convites(equipe, convidar)
        return equipe


def remover_membro(equipe, usuario_id):
    with transaction.atomic():
        edicao = _travar_edicao(equipe.edicao_id)
        _exigir_inscricao_aberta(edicao)
        if equipe.criador_id == usuario_id:
            raise ValidationError({'detail': 'O criador não pode ser removido; exclua a equipe se necessário.'})
        vinculo = equipe.participantes.filter(user_id=usuario_id).first()
        if vinculo is None:
            raise ValidationError({'detail': 'Este usuário não faz parte da equipe.'})
        vinculo.delete()


def excluir_equipe(equipe):
    with transaction.atomic():
        edicao = _travar_edicao(equipe.edicao_id)
        _exigir_inscricao_aberta(edicao)
        projeto = equipe.projeto
        try:
            equipe.participantes.all().delete()
            equipe.delete()
            projeto.delete()
        except ProtectedError:
            raise ValidationError({'detail': 'Não é possível excluir: há dados vinculados a esta equipe.'})
