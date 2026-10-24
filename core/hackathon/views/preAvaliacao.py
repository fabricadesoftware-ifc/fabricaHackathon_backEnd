from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import AvaliadorEdicao, PreAvaliacao, Projeto
from ..permissions import is_admin, is_professor
from ..serializers.preAvaliacao import PreAvaliacaoSerializer
from ..services.pre_avaliacao import (
    motivo_fechada, pre_avaliacao_aberta, salvar_com_pontuacao,
)


def _opcoes():
    return {
        "organizacao_metodo": [{"valor": v, "rotulo": r} for v, r in PreAvaliacao.Organizacao.choices],
        "hospedagem_plataforma": [{"valor": v, "rotulo": r} for v, r in PreAvaliacao.Hospedagem.choices],
        "banco_plataforma": [{"valor": v, "rotulo": r} for v, r in PreAvaliacao.Banco.choices],
    }


class PreAvaliacaoView(APIView):
    """
    Formulário de pré-avaliação do projeto (10% da nota final).
    GET: membros da equipe, administrador, professor e avaliadores da edição.
    PATCH/PUT: apenas o criador da equipe (os demais integrantes só visualizam), com a pré-avaliação liberada, no prazo e a edição em andamento.
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _carregar(self, request, projeto_id):
        projeto = get_object_or_404(Projeto.objects.select_related("edicao"), pk=projeto_id)
        equipe = getattr(projeto, "equipes", None)
        membros = []
        if equipe is not None:
            membros = list(equipe.participantes.select_related("user").order_by("id"))
        eh_membro = any(m.user_id == request.user.pk for m in membros)
        pode_ler = (
            eh_membro or is_admin(request.user) or is_professor(request.user)
            or AvaliadorEdicao.objects.filter(avaliador=request.user, edicao_id=projeto.edicao_id).exists()
        )
        if not pode_ler:
            raise PermissionDenied("Você não tem acesso à pré-avaliação deste projeto.")
        return projeto, membros, eh_membro

    @staticmethod
    def _eh_criador(request, projeto):
        equipe = getattr(projeto, "equipes", None)
        if equipe is None:
            return False
        if equipe.criador_id is None:  # equipe sem criador: qualquer integrante responde
            return equipe.participantes.filter(user_id=request.user.pk).exists()
        return equipe.criador_id == request.user.pk

    def _resposta(self, request, projeto, membros, pre):
        edicao = projeto.edicao
        dados = PreAvaliacaoSerializer(
            pre if pre is not None else PreAvaliacao(projeto=projeto), context={"request": request}
        ).data
        return {
            "projeto": projeto.pk,
            "edicao": edicao.pk,
            "aberta": pre_avaliacao_aberta(edicao),
            "motivo_fechada": motivo_fechada(edicao),
            "liberada": edicao.pre_avaliacao_liberada,
            "pode_editar": self._eh_criador(request, projeto),
            "prazo": edicao.prazo_pre_avaliacao,
            "preenchida": pre is not None,
            "integrantes": [
                {"id": m.user_id, "nome": m.user.get_full_name() or m.user.username} for m in membros
            ],
            "opcoes": _opcoes(),
            **dados,
        }

    def get(self, request, projeto_id):
        projeto, membros, _ = self._carregar(request, projeto_id)
        pre = PreAvaliacao.objects.filter(projeto=projeto).first()
        return Response(self._resposta(request, projeto, membros, pre))

    @transaction.atomic
    def patch(self, request, projeto_id):
        projeto, membros, eh_membro = self._carregar(request, projeto_id)
        if not eh_membro:
            raise PermissionDenied("Apenas integrantes da equipe podem acessar a pré-avaliação.")
        if not self._eh_criador(request, projeto):
            raise PermissionDenied("Só o criador da equipe responde a pré-avaliação; os demais integrantes apenas visualizam.")
        if not pre_avaliacao_aberta(projeto.edicao):
            raise PermissionDenied(motivo_fechada(projeto.edicao))
        pre, _ = PreAvaliacao.objects.select_for_update().get_or_create(projeto=projeto)
        serializer = PreAvaliacaoSerializer(
            pre, data=request.data, partial=True,
            context={"request": request, "membros_ids": [m.user_id for m in membros]},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        salvar_com_pontuacao(serializer.instance)
        return Response(self._resposta(request, projeto, membros, serializer.instance))

    put = patch
