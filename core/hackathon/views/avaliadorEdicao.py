from rest_framework.viewsets import ModelViewSet
from ..models import AvaliadorEdicao
from ..permissions import IsAdminOrReadOnly
from ..serializers import AvaliadorEdicaoSerializer, AvaliadorEdicaoListSerializer


class AvaliadorEdicaoViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = AvaliadorEdicao.objects.all().order_by('id')
    serializer_class = AvaliadorEdicaoSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return AvaliadorEdicaoListSerializer
        return super().get_serializer_class()


AvaliadorViewSet = AvaliadorEdicaoViewSet
