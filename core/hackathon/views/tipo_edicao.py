from rest_framework.viewsets import ModelViewSet

from ..models import TipoEdicao
from ..permissions import IsAdminOrReadOnly
from ..serializers import TipoEdicaoSerializer

class TipoEdicaoViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = TipoEdicao.objects.all()
    serializer_class = TipoEdicaoSerializer