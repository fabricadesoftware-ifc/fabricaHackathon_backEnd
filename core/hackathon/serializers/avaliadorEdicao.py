from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from ..models import AvaliadorEdicao
from ..validations.avaliador_edicao_validation import validate_avaliador_tipo


class AvaliadorEdicaoSerializer(ModelSerializer):
    class Meta:
        model = AvaliadorEdicao
        fields = ['id', 'user', 'edicao']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=AvaliadorEdicao.objects.all(),
                fields=['user', 'edicao'],
                message="Este usuário já está vinculado como avaliador nesta edição."
            )
        ]

    def validate_user(self, value):
        validate_avaliador_tipo(value)
        return value


class AvaliadorEdicaoListSerializer(ModelSerializer):
    class Meta:
        model = AvaliadorEdicao
        fields = ['id', 'user', 'edicao']

