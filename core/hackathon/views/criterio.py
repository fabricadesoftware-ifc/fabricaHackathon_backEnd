from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from ..models import Criterio
from ..serializers import CriterioSerializer

class CriterioViewSet(ModelViewSet):
    queryset = Criterio.objects.all()
    serializer_class = CriterioSerializer