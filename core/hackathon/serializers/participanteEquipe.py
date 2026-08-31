from rest_framework.serializers import ModelSerializer
from ..models import participanteEquipe

class ParticipanteEquipeSerializer(ModelSerializer):
    class Meta:
        model = participanteEquipe
        fields = ['id', 'user', 'equipe']
        