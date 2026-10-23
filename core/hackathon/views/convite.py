from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..permissions import IsParticipante
from ..serializers.inscricao import MinhaEquipeSerializer
from ..services import convites as servico


class ConviteInfoView(APIView):
    """GET /api/convites/<token>/ — dados públicos para a tela de convite (sem login)."""

    permission_classes = [AllowAny]

    def get(self, request, token):
        convite = servico.obter_por_token(token)
        equipe = convite.equipe
        valido, motivo = servico.situacao(convite)
        criador = equipe.criador
        return Response({
            "valido": valido,
            "motivo": motivo,
            "equipe": equipe.nome_equipe,
            "edicao": equipe.edicao.nome,
            "criador": (criador.get_full_name().strip() or criador.email) if criador else None,
        })


class ConviteAceitarView(APIView):
    """POST /api/convites/<token>/aceitar/ — o participante logado entra na equipe."""

    permission_classes = [IsParticipante]

    def post(self, request, token):
        equipe = servico.aceitar(request.user, token)
        equipe = type(equipe).objects.prefetch_related("participantes__user", "convites").get(pk=equipe.pk)
        return Response(MinhaEquipeSerializer(equipe, context={"request": request}).data)
