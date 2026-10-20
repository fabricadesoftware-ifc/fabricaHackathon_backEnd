from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.viewsets import ReadOnlyModelViewSet

from ..models import SolicitacaoPerfil
from ..permissions import IsAdmin
from ..query_params import int_param
from ..serializers.registro import RegistroSerializer, SolicitacaoPerfilSerializer


class RegistroView(CreateAPIView):
    """Cadastro público: sempre cria PARTICIPANTE; perfil_solicitado gera uma solicitação pendente."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]
    serializer_class = RegistroSerializer


class SolicitacaoPerfilViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = SolicitacaoPerfilSerializer
    queryset = SolicitacaoPerfil.objects.select_related('usuario', 'decidida_por')

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            valor = self.request.query_params.get('status')
            if valor:
                if valor not in SolicitacaoPerfil.Status.values:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError(
                        {'status': f"Valor inválido. Use um de: {', '.join(SolicitacaoPerfil.Status.values)}."}
                    )
                queryset = queryset.filter(status=valor)
            usuario = int_param(self.request, 'usuario')
            if usuario is not None:
                queryset = queryset.filter(usuario_id=usuario)
        return queryset

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        solicitacao = self.get_object()
        solicitacao.aprovar(request.user)
        return Response(self.get_serializer(solicitacao).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        solicitacao = self.get_object()
        solicitacao.recusar(request.user)
        return Response(self.get_serializer(solicitacao).data, status=status.HTTP_200_OK)
