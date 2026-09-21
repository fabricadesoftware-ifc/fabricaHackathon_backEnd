from rest_framework.viewsets import ModelViewSet
from ..models import AvaliadorEdicao
from ..serializers import AvaliadorEdicaoSerializer, AvaliadorEdicaoListSerializer


class AvaliadorEdicaoViewSet(ModelViewSet):
    queryset = AvaliadorEdicao.objects.all().order_by('id')
    serializer_class = AvaliadorEdicaoSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return AvaliadorEdicaoListSerializer
        return super().get_serializer_class()


AvaliadorViewSet = AvaliadorEdicaoViewSet
