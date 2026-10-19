import logging

logger = logging.getLogger(__name__)


class LimpaImagensAntigasMixin:
    """
    Apaga do storage a imagem anterior quando ela é substituída ou removida.
    Falha ao apagar é apenas registrada e nunca derruba a requisição.
    Defina `campos_imagem` com os nomes dos campos de imagem do modelo.
    """

    campos_imagem = ()

    def update(self, instance, validated_data):
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
