"""Serializers de leitura pública: nunca expõem participantes, usuários ou e-mails."""
from rest_framework import serializers

from ..models import Criterio, Edicao, Equipe, Projeto, Tema
from .apoiador import ApoiadorListSerializer
from .edicao import EdicaoListSerializer


def nota_final_publica(projeto):
    """A nota só é divulgada quando a edição está FINALIZADO."""
    if projeto.edicao.status != "FINALIZADO":
        return None
    nota = projeto.notaFinal_projeto
    # Decimal como string com 2 casas, igual ao padrão do DRF (ex.: "9.50").
    return None if nota is None else f"{nota:.2f}"


class CriterioPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Criterio
        fields = ["id", "nome"]


class TemaPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tema
        fields = ["id", "descricao_tema"]


class ProjetoResumoSerializer(serializers.ModelSerializer):
    nota_final = serializers.SerializerMethodField()

    class Meta:
        model = Projeto
        fields = ["id", "nome_projeto", "descricao_projeto", "link_deploy_projeto", "nota_final"]

    def get_nota_final(self, projeto):
        return nota_final_publica(projeto)


class EquipePublicSerializer(serializers.ModelSerializer):
    tema = serializers.CharField(source="tema.descricao_tema", read_only=True)
    projeto = ProjetoResumoSerializer(read_only=True)

    class Meta:
        model = Equipe
        fields = ["id", "nome_equipe", "edicao", "tema", "projeto"]


class ProjetoPublicSerializer(serializers.ModelSerializer):
    nome_equipe = serializers.CharField(source="equipes.nome_equipe", read_only=True, default=None)
    nota_final = serializers.SerializerMethodField()

    class Meta:
        model = Projeto
        fields = [
            "id",
            "nome_projeto",
            "descricao_projeto",
            "link_deploy_projeto",
            "edicao",
            "nome_equipe",
            "nota_final",
        ]

    def get_nota_final(self, projeto):
        return nota_final_publica(projeto)


class EdicaoDetailPublicSerializer(EdicaoListSerializer):
    apoiadores = ApoiadorListSerializer(many=True, read_only=True)
    criterios = CriterioPublicSerializer(many=True, read_only=True)
    temas = TemaPublicSerializer(many=True, read_only=True)
    equipes = EquipePublicSerializer(many=True, read_only=True)

    class Meta(EdicaoListSerializer.Meta):
        fields = EdicaoListSerializer.Meta.fields + [
            "descricao",
            "minimo_participantes",
            "maximo_participantes",
            "maximo_equipes",
            "apoiadores",
            "criterios",
            "temas",
            "equipes",
        ]


class RankingSerializer(serializers.Serializer):
    posicao = serializers.IntegerField()
    projeto = serializers.CharField()
    projeto_id = serializers.IntegerField()
    equipe = serializers.CharField(allow_null=True)
    nota_final = serializers.DecimalField(max_digits=4, decimal_places=2)
