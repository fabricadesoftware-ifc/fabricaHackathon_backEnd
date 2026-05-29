from rest_framework.viewsets import ModelViewSet
from ..models import Projeto
from ..serializers import ProjetoListSerializer, ProjetoSerializer

class ProjetoViewSet(ModelViewSet):
    queryset = Projeto.objects.all()
    
    def get_serializer_class(self):
        if self.action == "list":
            return ProjetoListSerializer
    
        return ProjetoSerializer