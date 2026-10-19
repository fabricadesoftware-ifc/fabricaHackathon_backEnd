from rest_framework.viewsets import ModelViewSet
from ..models import Criterio
from ..permissions import IsAdminOrReadOnly
from ..serializers import CriterioSerializer

class CriterioViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Criterio.objects.all()
    serializer_class = CriterioSerializer