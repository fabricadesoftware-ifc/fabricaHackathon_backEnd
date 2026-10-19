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
            "local",
            "responsavel",
            "minimo_participantes",
            "maximo_participantes",
            "maximo_equipes",
            "tipo_edicao",
            "apoiadores"
        ]

    def validate(self, data):
        return validate_edicao(data)

class EdicaoListSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    tipo_edicao = serializers.CharField(source="tipo_edicao.nome", read_only=True)
    total_equipes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Edicao
        fields = [
            "id",
            "nome",
            "ano",
            "status",
            "status_label",
            "data_inicio",
            "data_fim",
            "local",
            "responsavel",
            "tipo_edicao",
            "total_equipes",
        ]
