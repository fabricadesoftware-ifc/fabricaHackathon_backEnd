from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from ..models import Nota
from ..serializers import (
    NotaSerializer,
    NotaListSerializer,
    NotaLoteSerializer,
)

class NotaViewSet(ModelViewSet):
    queryset = Nota.objects.all()
    serializer_class = NotaSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return NotaListSerializer
        elif self.action == 'lote':
            return NotaLoteSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['post'], url_path='lote')
    def lote(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notas_criadas = serializer.save()
        return Response(
            NotaSerializer(notas_criadas, many=True).data,
            status=status.HTTP_201_CREATED
        )