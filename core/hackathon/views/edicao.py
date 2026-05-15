from rest_framework.viewsets import ModelViewSet
from ..models import Edicao
from ..serializers import EdicaoSerializer
from ..serializers import EdicaoListSerializer


class EdicaoViewSet(ModelViewSet):
    queryset = Edicao.objects.all()
    serializer_class = EdicaoSerializer
        
    def get_serializer_class(self):
        if self.action == 'list':
            return EdicaoListSerializer
        return super().get_serializer_class()
    