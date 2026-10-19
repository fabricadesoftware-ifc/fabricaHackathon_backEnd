from rest_framework.viewsets import ModelViewSet
from ..models import Criterio
from ..permissions import ReadOnlyOrAuthenticated
from ..serializers import CriterioSerializer

class CriterioViewSet(ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = Criterio.objects.all()
    serializer_class = CriterioSerializer
