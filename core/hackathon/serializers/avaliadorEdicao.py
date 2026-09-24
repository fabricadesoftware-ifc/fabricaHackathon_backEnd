from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from ..models import AvaliadorEdicao
from ..validations.avaliador_edicao_validation import validate_avaliador_tipo


class AvaliadorSerializer(ModelSerializer):
    class Meta:
        model = AvaliadorEdicao
        fields = ['id', 'avaliador', 'edicao']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=AvaliadorEdicao.objects.all(),
                fields=['avaliador', 'edicao'],
                message="Este usuário já está vinculado como avaliador nesta edição."
            )
        ]

    def validate_avaliador(self, value):
        validate_avaliador_tipo(value)
        return value


class AvaliadorListSerializer(ModelSerializer):
    class Meta:
        model = AvaliadorEdicao
        fields = ['id', 'avaliador', 'edicao']


AvaliadorEdicaoSerializer = AvaliadorSerializer
AvaliadorEdicaoListSerializer = AvaliadorListSerializer
