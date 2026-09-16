from rest_framework.serializers import ModelSerializer
from ..models import ParticipanteEquipe

class ParticipanteEquipeSerializer(ModelSerializer):
    class Meta:
        model = ParticipanteEquipe
        fields = ['user', 'equipe']

class ParticipanteEquipeListSerializer(ModelSerializer):
    class Meta:
        model = ParticipanteEquipe
        fields = ['id', 'user', 'equipe']