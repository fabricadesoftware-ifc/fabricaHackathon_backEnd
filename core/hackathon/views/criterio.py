from rest_framework.viewsets import ModelViewSet

from ..models import Criterio
from ..serializers import CriterioSerializer

class CriterioViewSet(ModelViewSet):
    queryset = Criterio.objects.all()
    serializer_class = CriterioSerializer