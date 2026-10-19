from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet
from ..models import Projeto
from ..permissions import ReadOnlyOrAuthenticated
from ..query_params import int_param
from ..serializers import ProjetoSerializer
from ..serializers.public import ProjetoPublicSerializer

class ProjetoViewSet(ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = Projeto.objects.all()
    serializer_class = ProjetoSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome_projeto']
    ordering_fields = ['nome_projeto', 'id']
    ordering = ['nome_projeto', 'id']

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ProjetoPublicSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action not in ('list', 'retrieve'):
            return queryset
        queryset = queryset.select_related('edicao', 'equipes')
        edicao = int_param(self.request, 'edicao')
        if self.action == 'list' and edicao is not None:
            queryset = queryset.filter(edicao_id=edicao)
        return queryset
