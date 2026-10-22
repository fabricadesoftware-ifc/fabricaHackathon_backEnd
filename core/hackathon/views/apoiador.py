from rest_framework.viewsets import ModelViewSet

from ..models import Apoiador
from ..permissions import ReadOnlyOrAuthenticated
from ..serializers import ApoiadorSerializer

class ApoiadorViewSet(ModelViewSet):
    permission_classes = [ReadOnlyOrAuthenticated]
    queryset = Apoiador.objects.all()
    serializer_class = ApoiadorSerializer
