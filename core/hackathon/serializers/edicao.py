from rest_framework import serializers
from ..models import Edicao
from ..validations.edicao_validation import validate_edicao
from ..serializers import ApoiadorListSerializer
class EdicaoSerializer(serializers.ModelSerializer):
    apoiadores = ApoiadorListSerializer(many=True, read_only=True)

    class Meta:
        model = Edicao
        fields = [
            "id",
            "nome",
            "ano",
            "descricao",
            "status",
            "data_inicio",
            "data_fim",
            "minimo_participantes",
            "maximo_participantes",
            "maximo_equipes",
            "tipo_edicao",
            "apoiadores"
        ]
        
    def validate(self, data):
        return validate_edicao(data)

class EdicaoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edicao
        fields = ["nome", "ano",]
            