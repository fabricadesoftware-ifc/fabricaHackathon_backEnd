from rest_framework.viewsets import ModelViewSet
from ..models import Nota
from ..serializers import (
    NotaSerializer,
    NotaListSerializer
)

class NotaViewSet(ModelViewSet):
    queryset = Nota.objects.all()
    serializer_class = NotaSerializer
        
    def get_serializer_class(self):
        if self.action == 'list':
            return NotaListSerializer
        return super().get_serializer_class()