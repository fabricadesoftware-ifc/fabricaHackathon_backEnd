from rest_framework.viewsets import ModelViewSet
from ..models import Edicao
from ..serializers import EdicaoSerializer
from ..serializers import EdicaoListSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class EdicaoViewSet(ModelViewSet):
    queryset = Edicao.objects.all()
    serializer_class = EdicaoSerializer
        
    def get_serializer_class(self):
        if self.action == 'list':
            return EdicaoListSerializer
        return super().get_serializer_class()
    
    def get_permissions(self):
        if self.action in ["create", "update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]