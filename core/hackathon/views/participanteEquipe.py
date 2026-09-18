from rest_framework.viewsets import ModelViewSet
from ..models import ParticipanteEquipe
from ..serializers import ParticipanteEquipeSerializer, ParticipanteEquipeListSerializer

class ParticipanteEquipeViewSet(ModelViewSet):
    queryset = ParticipanteEquipe.objects.all()
    serializer_class = ParticipanteEquipeSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ParticipanteEquipeListSerializer
        return super().get_serializer_class()
