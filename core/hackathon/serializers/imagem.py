import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import APIException, ValidationError

logger = logging.getLogger(__name__)


class LimpaImagensAntigasMixin:
    """
    Apaga do storage a imagem anterior quando ela é substituída ou removida.
    Falha ao apagar é apenas registrada e nunca derruba a requisição.
    Defina `campos_imagem` com os nomes dos campos de imagem do modelo.
    """

    campos_imagem = ()

    def _gravar(self, operacao, validated_data, *args):
        """Falha do storage (ex.: Cloudinary fora do ar/credencial errada) vira erro 400 legível, não 500."""
        enviando = [c for c in self.campos_imagem if validated_data.get(c)]
        try:
            return operacao(*args, validated_data)
        except (APIException, DjangoValidationError):
            raise
        except Exception:
            if not enviando:
                raise
            logger.exception("Falha ao gravar imagem (%s) no storage.", ", ".join(enviando))
            raise ValidationError({
                enviando[0]: "Não foi possível salvar o arquivo agora. Tente novamente em instantes ou use outro arquivo."
            })

    def create(self, validated_data):
        return self._gravar(super().create, validated_data)

    def update(self, instance, validated_data):
        return self._gravar(self._atualizar, validated_data, instance)

    def _atualizar(self, instance, validated_data):
        antigos = {
            campo: getattr(instance, campo)
            for campo in self.campos_imagem
            if campo in validated_data and getattr(instance, campo)
        }
        antigos = {campo: (arquivo.storage, arquivo.name) for campo, arquivo in antigos.items()}
        instance = super().update(instance, validated_data)
        for campo, (storage, nome) in antigos.items():
            atual = getattr(instance, campo)
            if atual and atual.name == nome:
                continue
            try:
                storage.delete(nome)
            except Exception:
                logger.exception("Falha ao apagar imagem antiga %r do storage.", nome)
        return instance
