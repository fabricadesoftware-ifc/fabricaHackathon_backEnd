from rest_framework.viewsets import ModelViewSet
from ..models import Equipe
from ..serializers import EquipeSerializer, EquipeListSerializer

class EquipeViewSet(ModelViewSet):
    queryset = Equipe.objects.all()
    serializer_class = EquipeSerializer
    def get_serializer_class(self):
        if self.action == 'list':
            return EquipeListSerializer
        return super().get_serializer_class()