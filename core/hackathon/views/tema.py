from rest_framework.viewsets import ModelViewSet
from ..models import Tema
from ..permissions import ReadOnlyOrAuthenticated
from ..query_params import int_param
from ..serializers import TemaSerializer

class TemaViewSet(ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = Tema.objects.all()
    serializer_class = TemaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        edicao_id = int_param(self.request, 'edicao_id')

        if edicao_id is not None:
            queryset = queryset.filter(edicao_id=edicao_id)

        return queryset
