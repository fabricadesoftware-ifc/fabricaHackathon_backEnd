from rest_framework.viewsets import ModelViewSet

from ..models import TipoEdicao
from ..serializers import TipoEdicaoSerializer

class TipoEdicaoViewSet(ModelViewSet):
    queryset = TipoEdicao.objects.all()
    serializer_class = TipoEdicaoSerializer