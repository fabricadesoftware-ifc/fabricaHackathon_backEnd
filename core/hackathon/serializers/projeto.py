from rest_framework.serializers import ModelSerializer
from ..models import Projeto
from .imagem import LimpaImagensAntigasMixin

class ProjetoSerializer(LimpaImagensAntigasMixin, ModelSerializer):
    campos_imagem = ("logo_projeto",)

    class Meta:
        model = Projeto
        fields = [
            "id",
            "nome_projeto",
            "descricao_projeto",
            "link_deploy_projeto",
            "logo_projeto",
            "notaFinal_projeto",
            "edicao"
        ]
        read_only_fields = ["notaFinal_projeto"]

class ProjetoListSerializer(ModelSerializer):
    class Meta:
        model = Projeto
        fields = [
            "id",
            "nome_projeto",
            "notaFinal_projeto",
            "edicao"
        ]