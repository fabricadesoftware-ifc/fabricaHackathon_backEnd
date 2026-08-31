from rest_framework.viewsets import ModelViewSet
from ..models import participanteEquipearticipanteEquipe
from ..serializers import ParticipanteEquipeSerializer

class ParticipanteEquipeViewSet(ModelViewSet):
    queryset = participanteEquipe.objects.all()
    serializer_class = ParticipanteEquipeSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ParticipanteEquipeListSerializer
        return super().get_serializer_class()
