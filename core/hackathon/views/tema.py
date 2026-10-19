from rest_framework.viewsets import ModelViewSet
from ..models import Tema
from ..permissions import IsAdminOrReadOnly
from ..serializers import TemaSerializer

class TemaViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Tema.objects.all()
    serializer_class = TemaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
    
        edicao_id = self.request.query_params.get('edicao_id')

        if edicao_id:
            queryset = queryset.filter(edicao_id=edicao_id)

        return queryset