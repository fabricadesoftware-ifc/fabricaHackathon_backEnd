from rest_framework import serializers
from ..models import Tema

class TemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tema
        fields = [
            'id',
            'descricao_tema',
            'edicao'
        ]