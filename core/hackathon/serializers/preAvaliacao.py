from urllib.parse import urlparse

from rest_framework import serializers

from ..models import PreAvaliacao
from .imagem import LimpaImagensAntigasMixin

CAMPOS_LINK = ("organizacao_link", "arquitetura_link", "hospedagem_link")


class PreAvaliacaoSerializer(LimpaImagensAntigasMixin, serializers.ModelSerializer):
    campos_imagem = ("arquivo_rfs_rnfs", "arquitetura_arquivo")

    class Meta:
        model = PreAvaliacao
        fields = [
            "responsabilidades", "organizacao_metodo", "organizacao_link",
            "problema_entendido", "problema_explicacao", "maior_dificuldade", "proximos_passos",
            "arquivo_rfs_rnfs", "arquitetura_arquivo", "arquitetura_link",
            "hospedagem_plataforma", "hospedagem_link", "hospedagem_justificativa",
            "banco_plataforma", "banco_justificativa",
            "nota", "detalhe_pontuacao", "atualizada_em",
        ]
        read_only_fields = ["nota", "detalhe_pontuacao", "atualizada_em"]

    def _validar_link(self, valor):
        if valor and urlparse(valor).scheme not in ("http", "https"):
            raise serializers.ValidationError("Informe um link começando com http:// ou https://.")
        return valor

    def validate_organizacao_link(self, valor):
        return self._validar_link(valor)

    def validate_arquitetura_link(self, valor):
        return self._validar_link(valor)

    def validate_hospedagem_link(self, valor):
        return self._validar_link(valor)

    def validate_responsabilidades(self, valor):
        membros = set(self.context.get("membros_ids", []))
        if not isinstance(valor, list):
            raise serializers.ValidationError("Envie uma lista de {user, area}.")
        vistos = set()
        for entrada in valor:
            if not isinstance(entrada, dict) or set(entrada) - {"user", "area"}:
                raise serializers.ValidationError("Cada item deve ter apenas 'user' e 'area'.")
            usuario, area = entrada.get("user"), str(entrada.get("area", "")).strip()
            if usuario not in membros:
                raise serializers.ValidationError(f"O usuário {usuario} não faz parte da equipe.")
            if usuario in vistos:
                raise serializers.ValidationError(f"O usuário {usuario} aparece mais de uma vez.")
            if not area or len(area) > 60:
                raise serializers.ValidationError("A área deve ter de 1 a 60 caracteres.")
            vistos.add(usuario)
            entrada["area"] = area
        return valor
