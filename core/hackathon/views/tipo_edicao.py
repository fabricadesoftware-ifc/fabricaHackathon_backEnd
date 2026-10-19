from rest_framework.viewsets import ModelViewSet

from ..models import TipoEdicao
from ..permissions import ReadOnlyOrAuthenticated
from ..serializers import TipoEdicaoSerializer

class TipoEdicaoViewSet(ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = TipoEdicao.objects.all()
    serializer_class = TipoEdicaoSerializer
