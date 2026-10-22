from rest_framework import serializers
from ..models import Edicao
from ..validations.edicao_validation import (
    validate_edicao,
    validate_limites_com_instancia,
    validate_transicao_status,
)
from ..serializers import ApoiadorListSerializer
from .imagem import LimpaImagensAntigasMixin
class EdicaoSerializer(LimpaImagensAntigasMixin, serializers.ModelSerializer):
    campos_imagem = ("imagem_capa",)
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
            "imagem_capa",
            "minimo_participantes",
            "maximo_participantes",
            "maximo_equipes",
            "pre_avaliacao_liberada",
            "prazo_pre_avaliacao",
            "tipo_edicao",
            "apoiadores"
        ]

    def validate(self, data):
        validate_transicao_status(self.instance, data)
        validate_limites_com_instancia(self.instance, data)
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
            "imagem_capa",
            "tipo_edicao",
            "total_equipes",
        ]
