from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet
from ..models import Equipe
from ..permissions import ReadOnlyOrAuthenticated
from ..query_params import int_param
from .mixins import BloqueiaEdicaoFinalizadaMixin
from ..serializers import EquipeSerializer
from ..serializers.public import EquipePublicSerializer

class EquipeViewSet(BloqueiaEdicaoFinalizadaMixin, ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = Equipe.objects.all()
    serializer_class = EquipeSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome_equipe']
    ordering_fields = ['nome_equipe', 'id']
    ordering = ['nome_equipe', 'id']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return EquipePublicSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action not in ('list', 'retrieve'):
            return queryset
        queryset = queryset.select_related('tema', 'projeto__edicao')
        edicao = int_param(self.request, 'edicao')
        if self.action == 'list' and edicao is not None:
            queryset = queryset.filter(edicao_id=edicao)
        return queryset
