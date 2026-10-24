"""Painel de controle do administrador: visões agregadas por edição (somente ADMIN)."""
from decimal import Decimal

from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import (
    AvaliadorEdicao, Criterio, Edicao, Equipe, Nota, ParticipanteEquipe, PreAvaliacao, Projeto, Tema, User,
)
from ..models.user import tipoUser
from ..permissions import IsAdmin
from .mixins import bloquear_se_finalizada


def _nome(user):
    return user.get_full_name().strip() or user.username


def _dec(valor):
    return None if valor is None else f"{Decimal(valor).quantize(Decimal('0.01'))}"


def _contagens(edicao):
    equipes = Equipe.objects.filter(edicao=edicao)
    return {
        "equipes": equipes.filter(organizadora=False).count(),
        "equipes_fabrica": equipes.filter(organizadora=True).count(),
        "maximo_equipes": edicao.maximo_equipes,
        "participantes": ParticipanteEquipe.objects.filter(equipe__edicao=edicao).count(),
        "avaliadores": AvaliadorEdicao.objects.filter(edicao=edicao).count(),
        "criterios": Criterio.objects.filter(edicao=edicao).count(),
        "temas": Tema.objects.filter(edicao=edicao).count(),
        "pre_avaliacoes_preenchidas": PreAvaliacao.objects.filter(projeto__edicao=edicao).count(),
    }


def _dados_edicao(edicao):
    return {
        "id": edicao.id,
        "nome": edicao.nome,
        "ano": edicao.ano,
        "descricao": edicao.descricao or "",
        "status": edicao.status,
        "status_label": edicao.get_status_display(),
        "data_inicio": edicao.data_inicio,
        "data_fim": edicao.data_fim,
        "local": edicao.local,
        "responsavel": edicao.responsavel,
        "tipo_edicao": edicao.tipo_edicao_id,
        "tipo_edicao_nome": edicao.tipo_edicao.nome,
        "minimo_participantes": edicao.minimo_participantes,
        "maximo_participantes": edicao.maximo_participantes,
        "maximo_equipes": edicao.maximo_equipes,
        "pre_avaliacao_liberada": edicao.pre_avaliacao_liberada,
        "prazo_pre_avaliacao": edicao.prazo_pre_avaliacao,
    }


def _progresso_avaliadores(edicao):
    """Notas lançadas x esperadas (projetos x critérios) por avaliador vinculado."""
    projetos = Projeto.objects.filter(edicao=edicao).exclude(equipes__organizadora=True).count()
    criterios = Criterio.objects.filter(edicao=edicao).count()
    esperadas = projetos * criterios
    lancadas = dict(
        Nota.objects.filter(avaliador__edicao=edicao).values_list("avaliador_id").annotate(c=Count("id"))
    )
    itens = []
    for vinculo in AvaliadorEdicao.objects.filter(edicao=edicao).select_related("avaliador").order_by("id"):
        itens.append({
            "vinculo_id": vinculo.id,
            "user_id": vinculo.avaliador_id,
            "nome": _nome(vinculo.avaliador),
            "email": vinculo.avaliador.email,
            "notas_lancadas": lancadas.get(vinculo.id, 0),
            "notas_esperadas": esperadas,
        })
    return itens


class PainelEdicoesView(APIView):
    """GET /api/painel/edicoes/ — todas as edições com contadores."""

    permission_classes = [IsAdmin]

    def get(self, request):
        itens = []
        for edicao in Edicao.objects.select_related("tipo_edicao").order_by("-data_inicio", "-id"):
            itens.append({**_dados_edicao(edicao), "contagens": _contagens(edicao)})
        return Response(itens)


class PainelEdicaoView(APIView):
    """GET /api/painel/edicoes/{id}/ — resumo da edição: dados, contagens, critérios, temas e avaliadores."""

    permission_classes = [IsAdmin]

    def get(self, request, pk):
        edicao = get_object_or_404(Edicao.objects.select_related("tipo_edicao"), pk=pk)
        return Response({
            **_dados_edicao(edicao),
            "contagens": _contagens(edicao),
            "criterios": list(Criterio.objects.filter(edicao=edicao).order_by("id").values("id", "nome")),
            "temas": list(Tema.objects.filter(edicao=edicao).order_by("id").values("id", "descricao_tema")),
            "avaliadores": _progresso_avaliadores(edicao),
        })


class PainelEquipesView(APIView):
    """GET /api/painel/edicoes/{id}/equipes/ — equipes com membros, tema, projeto e pré-avaliação."""

    permission_classes = [IsAdmin]

    def get(self, request, pk):
        edicao = get_object_or_404(Edicao, pk=pk)
        equipes = (
            Equipe.objects.filter(edicao=edicao)
            .select_related("tema", "projeto", "criador")
            .prefetch_related("participantes__user")
            .order_by("nome_equipe")
        )
        pre = {p.projeto_id: p for p in PreAvaliacao.objects.filter(projeto__edicao=edicao)}
        itens = []
        for equipe in equipes:
            projeto = equipe.projeto
            p = pre.get(projeto.id)
            membros = list(equipe.participantes.all())
            itens.append({
                "id": equipe.id,
                "organizadora": equipe.organizadora,
                "nome_equipe": equipe.nome_equipe,
                "abaixo_do_minimo": len(membros) < edicao.minimo_participantes,
                "tema": equipe.tema.descricao_tema if equipe.tema else None,
                "criador": _nome(equipe.criador) if equipe.criador else None,
                "membros": [
                    {"id": v.user_id, "nome": _nome(v.user), "email": v.user.email}
                    for v in membros
                ],
                "projeto": {
                    "id": projeto.id,
                    "nome_projeto": projeto.nome_projeto,
                    "descricao_projeto": projeto.descricao_projeto,
                    "link_deploy_projeto": projeto.link_deploy_projeto,
                    "logo_projeto": request.build_absolute_uri(projeto.logo_projeto.url) if projeto.logo_projeto else None,
                },
                "pre_avaliacao": {"preenchida": p is not None, "nota": _dec(p.nota) if p else None},
                "nota_final": _dec(projeto.notaFinal_projeto),
            })
        return Response(itens)


class PainelResultadosView(APIView):
    """GET /api/painel/edicoes/{id}/resultados/ — notas por critério/avaliador e média final (visível ao admin sempre)."""

    permission_classes = [IsAdmin]

    def get(self, request, pk):
        edicao = get_object_or_404(Edicao, pk=pk)
        criterios = list(Criterio.objects.filter(edicao=edicao).order_by("id"))
        vinculos = list(AvaliadorEdicao.objects.filter(edicao=edicao).select_related("avaliador").order_by("id"))
        notas = list(Nota.objects.filter(projeto__edicao=edicao, projeto__equipes__organizadora=False))

        por_projeto = {}
        for n in notas:
            por_projeto.setdefault(n.projeto_id, []).append(n)

        pre = {p.projeto_id: p.nota for p in PreAvaliacao.objects.filter(projeto__edicao=edicao)}

        linhas = []
        for equipe in Equipe.objects.filter(edicao=edicao, organizadora=False).select_related("projeto").order_by("nome_equipe"):
            projeto = equipe.projeto
            ns = por_projeto.get(projeto.id, [])

            por_criterio = []
            for c in criterios:
                vals = [x.nota for x in ns if x.criterio_id == c.id]
                por_criterio.append({
                    "criterio_id": c.id, "criterio": c.nome,
                    "media": _dec(sum(vals) / len(vals)) if vals else None,
                })

            por_avaliador = []
            for v in vinculos:
                vals = [x.nota for x in ns if x.avaliador_id == v.id]
                por_avaliador.append({
                    "user_id": v.avaliador_id, "nome": _nome(v.avaliador),
                    "avaliados": len(vals), "de": len(criterios),
                    "media": _dec(sum(vals) / len(vals)) if vals else None,
                })

            linhas.append({
                "projeto_id": projeto.id,
                "projeto": projeto.nome_projeto,
                "equipe": equipe.nome_equipe,
                "por_criterio": por_criterio,
                "por_avaliador": por_avaliador,
                "completo": bool(vinculos and criterios and all(a["avaliados"] == a["de"] for a in por_avaliador)),
                "nota_pre_avaliacao": _dec(pre.get(projeto.id)),
                "nota_final": _dec(projeto.notaFinal_projeto),
            })

        # Ranking: com nota final primeiro (maior→menor); depois os ainda incompletos.
        linhas.sort(key=lambda l: (l["nota_final"] is None, -(Decimal(l["nota_final"]) if l["nota_final"] else 0), l["projeto"]))
        posicao, anterior = 0, None
        for i, l in enumerate(linhas, start=1):
            if l["nota_final"] is None:
                l["posicao"] = None
                continue
            if l["nota_final"] != anterior:
                posicao, anterior = i, l["nota_final"]
            l["posicao"] = posicao

        return Response({
            "edicao": {"id": edicao.id, "nome": edicao.nome, "status": edicao.status},
            "criterios": [{"id": c.id, "nome": c.nome} for c in criterios],
            "avaliadores": [{"user_id": v.avaliador_id, "nome": _nome(v.avaliador)} for v in vinculos],
            "resultados": linhas,
        })


class PainelAvaliadoresView(APIView):
    """
    GET  /api/painel/edicoes/{id}/avaliadores/        — todos os usuários Avaliador, com `vinculado` nesta edição.
    POST /api/painel/edicoes/{id}/avaliadores/        — {"user": id} vincula.
    DELETE /api/painel/edicoes/{id}/avaliadores/{user_id}/ — desvincula (só se ainda não lançou notas).
    """

    permission_classes = [IsAdmin]

    def get(self, request, pk):
        edicao = get_object_or_404(Edicao, pk=pk)
        vinculos = {v.avaliador_id: v for v in AvaliadorEdicao.objects.filter(edicao=edicao)}
        notas = dict(
            Nota.objects.filter(avaliador__edicao=edicao).values_list("avaliador__avaliador_id").annotate(c=Count("id"))
        )
        usuarios = User.objects.filter(tipoUser=tipoUser.avaliador).order_by("first_name", "email")
        return Response([
            {
                "user_id": u.id, "nome": _nome(u), "email": u.email,
                "vinculado": u.id in vinculos, "notas_lancadas": notas.get(u.id, 0),
            }
            for u in usuarios
        ])

    def post(self, request, pk):
        edicao = get_object_or_404(Edicao, pk=pk)
        bloquear_se_finalizada(edicao)
        user = get_object_or_404(User, pk=request.data.get("user"))
        if user.tipoUser != tipoUser.avaliador:
            raise ValidationError({"user": "Apenas usuários com perfil de Avaliador podem ser vinculados."})
        _, criado = AvaliadorEdicao.objects.get_or_create(avaliador=user, edicao=edicao)
        return Response({"user_id": user.id, "vinculado": True}, status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK)

    def delete(self, request, pk, user_id):
        edicao = get_object_or_404(Edicao, pk=pk)
        bloquear_se_finalizada(edicao)
        vinculo = get_object_or_404(AvaliadorEdicao, edicao=edicao, avaliador_id=user_id)
        if Nota.objects.filter(avaliador=vinculo).exists():
            raise ValidationError({"detail": "Este avaliador já lançou notas nesta edição e não pode ser desvinculado."})
        vinculo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PainelEquipeFabricaView(APIView):
    """
    POST /api/painel/edicoes/{id}/equipe-fabrica/ — cadastra a equipe da Fábrica (organizadora): fora da avaliação,
        do ranking e do limite de equipes. Aceita a qualquer momento antes de FINALIZADO.
        Corpo: {"nome_equipe", "nome_projeto", "descricao_projeto"?, "link_deploy_projeto"?, "membros"?: [e-mails de participantes]}
    PATCH /api/painel/edicoes/{id}/equipes/{equipe_id}/ — {"organizadora": true|false} marca/desmarca uma equipe existente.
    """

    permission_classes = [IsAdmin]

    @transaction.atomic
    def post(self, request, pk):
        edicao = get_object_or_404(Edicao.objects.select_for_update(), pk=pk)
        bloquear_se_finalizada(edicao)
        dados = request.data
        nome = (dados.get("nome_equipe") or "").strip()
        projeto_nome = (dados.get("nome_projeto") or "").strip()
        erros = {}
        if not nome:
            erros["nome_equipe"] = "Informe o nome da equipe."
        if not projeto_nome:
            erros["nome_projeto"] = "Informe o nome do projeto."
        if nome and Equipe.objects.filter(edicao=edicao, nome_equipe__iexact=nome).exists():
            erros["nome_equipe"] = "Já existe uma equipe com este nome nesta edição."
        usuarios = []
        mensagens = []
        for email in dados.get("membros") or []:
            usuario = User.objects.filter(email__iexact=str(email).strip()).first()
            if usuario is None:
                mensagens.append(f"Nenhum usuário cadastrado com o e-mail {email}.")
            elif usuario.tipoUser != tipoUser.participante:
                mensagens.append(f"O usuário {email} não tem perfil de Participante.")
            elif ParticipanteEquipe.objects.filter(user=usuario, equipe__edicao=edicao).exists():
                mensagens.append(f"O usuário {email} já faz parte de uma equipe nesta edição.")
            elif usuario in usuarios:
                mensagens.append(f"O e-mail {email} foi informado mais de uma vez.")
            else:
                usuarios.append(usuario)
        if mensagens:
            erros["membros"] = mensagens
        if len(usuarios) > edicao.maximo_participantes:
            erros["membros"] = [f"No máximo {edicao.maximo_participantes} participantes por equipe."]
        if erros:
            raise ValidationError(erros)

        projeto = Projeto.objects.create(
            edicao=edicao, nome_projeto=projeto_nome,
            descricao_projeto=(dados.get("descricao_projeto") or "").strip(),
            link_deploy_projeto=(dados.get("link_deploy_projeto") or None),
        )
        equipe = Equipe.objects.create(
            nome_equipe=nome, edicao=edicao, projeto=projeto, organizadora=True,
            criador=usuarios[0] if usuarios else None,
        )
        for usuario in usuarios:
            ParticipanteEquipe.objects.create(user=usuario, equipe=equipe)
        return Response({"id": equipe.id, "organizadora": True}, status=status.HTTP_201_CREATED)


class PainelEquipeMarcacaoView(APIView):
    permission_classes = [IsAdmin]

    @transaction.atomic
    def patch(self, request, pk, equipe_id):
        edicao = get_object_or_404(Edicao, pk=pk)
        bloquear_se_finalizada(edicao)
        equipe = get_object_or_404(Equipe.objects.select_related("projeto"), pk=equipe_id, edicao=edicao)
        if "organizadora" not in request.data:
            raise ValidationError({"organizadora": "Informe true ou false."})
        valor = request.data["organizadora"]
        equipe.organizadora = valor in (True, "true", "True", "1", 1)
        equipe.save(update_fields=["organizadora"])
        if equipe.organizadora:
            # sai da avaliação: apaga a nota final e as notas já lançadas para este projeto
            Nota.objects.filter(projeto=equipe.projeto).delete()
            Projeto.objects.filter(pk=equipe.projeto_id).update(notaFinal_projeto=None)
        else:
            from ..services.nota_final import recalcular_nota_final
            recalcular_nota_final(equipe.projeto)
        return Response({"id": equipe.id, "organizadora": equipe.organizadora})
