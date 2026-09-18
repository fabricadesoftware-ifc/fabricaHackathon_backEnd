from rest_framework.serializers import ModelSerializer
from ..models import ParticipanteEquipe
from ..validations.participante_equipe_validation import validate_participante_tipo

class ParticipanteEquipeSerializer(ModelSerializer):
    class Meta:
        model = ParticipanteEquipe
        fields = ['id', 'user', 'equipe']

    def validate_user(self, value):
        validate_participante_tipo(value)
        return value

class ParticipanteEquipeListSerializer(ModelSerializer):
    class Meta:
        model = ParticipanteEquipe
        fields = ['id', 'user', 'equipe']