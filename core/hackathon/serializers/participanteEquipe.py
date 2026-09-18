from rest_framework.serializers import ModelSerializer
from ..models import ParticipanteEquipe
from ..validations.participante_equipe_validation import (
    validate_participante_tipo,
    validate_participante_edicao_unica,
)

class ParticipanteEquipeSerializer(ModelSerializer):
    class Meta:
        model = ParticipanteEquipe
        fields = ['id', 'user', 'equipe']

    def validate_user(self, value):
        validate_participante_tipo(value)
        return value

    def validate(self, attrs):
        user = attrs.get('user') or getattr(self.instance, 'user', None)
        equipe = attrs.get('equipe') or getattr(self.instance, 'equipe', None)
        if user and equipe:
            validate_participante_edicao_unica(user, equipe, instance=self.instance)
        return attrs

class ParticipanteEquipeListSerializer(ModelSerializer):
    class Meta:
        model = ParticipanteEquipe
        fields = ['id', 'user', 'equipe']