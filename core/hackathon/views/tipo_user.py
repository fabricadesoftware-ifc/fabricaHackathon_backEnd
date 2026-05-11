from rest_framework.viewsets import ModelViewSet

from ..serializers import TipoUserSerializer
from ..models import TipoUser

class TipoUserViewSet(ModelViewSet):
    queryset = TipoUser.objects.all()
    serializer_class = TipoUserSerializer
    