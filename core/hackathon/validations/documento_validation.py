import os

from django.core.exceptions import ValidationError

DOCUMENTO_TAMANHO_MAXIMO = 10 * 1024 * 1024
DOCUMENTO_EXTENSOES = {".pdf", ".doc", ".docx", ".md", ".txt", ".png", ".jpg", ".jpeg", ".webp"}


def validate_documento(arquivo):
    """Valida tamanho (10 MB) e extensão de documentos enviados pelas equipes."""
    if arquivo is None:
        return
    if arquivo.size > DOCUMENTO_TAMANHO_MAXIMO:
        raise ValidationError(
            f"O arquivo excede o tamanho máximo de {DOCUMENTO_TAMANHO_MAXIMO // (1024 * 1024)} MB."
        )
    extensao = os.path.splitext(arquivo.name or "")[1].lower()
    if extensao not in DOCUMENTO_EXTENSOES:
        permitidas = ", ".join(sorted(e.lstrip(".") for e in DOCUMENTO_EXTENSOES))
        raise ValidationError(f"Formato não suportado. Envie um destes: {permitidas}.")
