from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

# Limite de tamanho por imagem (em bytes). Ajuste aqui para mudar em todos os campos.
IMAGEM_TAMANHO_MAXIMO = 5 * 1024 * 1024

# Formatos aceitos (nome do formato detectado pelo Pillow pelo conteúdo do arquivo).
IMAGEM_FORMATOS_PERMITIDOS = {"JPEG", "PNG", "WEBP"}


def validate_imagem(arquivo):
    """Valida tamanho e formato real (pelo conteúdo, não pela extensão) de uma imagem."""
    if arquivo is None:
        return

    if arquivo.size > IMAGEM_TAMANHO_MAXIMO:
        maximo_mb = IMAGEM_TAMANHO_MAXIMO / (1024 * 1024)
        raise ValidationError(f"A imagem excede o tamanho máximo de {maximo_mb:g} MB.")

    try:
        arquivo.seek(0)
        with Image.open(arquivo) as imagem:
            formato = imagem.format
            imagem.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise ValidationError("O arquivo enviado não é uma imagem válida.")
    finally:
        arquivo.seek(0)

    if formato not in IMAGEM_FORMATOS_PERMITIDOS:
        raise ValidationError("Formato de imagem não suportado. Envie JPEG, PNG ou WebP.")
