from rest_framework.serializers import ModelSerializer
from ..models import Projeto

class ProjetoSerializer(ModelSerializer):
    class Meta:
        model = Projeto
        fields = [
            "id",
            "nome_projeto",
            "descricao_projeto",
            "link_deploy_projeto",
            "notaFinal_projeto",
            "edicao",
            "tema",
        ]

class ProjetoListSerializer(ModelSerializer):
    class Meta:
        model = Projeto
        fields = [
            "id",
            "nome_projeto",
            "notaFinal_projeto",
            "edicao",
            "tema",
        ]