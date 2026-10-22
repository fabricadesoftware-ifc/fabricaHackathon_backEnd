"""Diagnóstico do armazenamento de imagens: envia e apaga um arquivo de teste e mostra a URL gerada."""
import io

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from PIL import Image


class Command(BaseCommand):
    help = "Testa o upload de imagens (Cloudinary ou disco) sem expor credenciais."

    def handle(self, *args, **options):
        import os

        usa_cloudinary = bool(os.environ.get("CLOUDINARY_URL"))
        self.stdout.write(f"Storage: {settings.STORAGES['default']['BACKEND']}")
        self.stdout.write(f"CLOUDINARY_URL definida: {'sim' if usa_cloudinary else 'NÃO'}")
        buf = io.BytesIO()
        Image.new("RGB", (8, 8), "blue").save(buf, "PNG")
        try:
            nome = default_storage.save("hackathon/_diagnostico/teste.png", ContentFile(buf.getvalue()))
            self.stdout.write(self.style.SUCCESS(f"Upload OK: {nome}"))
            self.stdout.write(f"URL: {default_storage.url(nome)}")
            try:
                default_storage.delete(nome)
                self.stdout.write("Arquivo de teste apagado.")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Upload ok, mas não consegui apagar: {type(e).__name__}: {e}"))
        except Exception as e:
            raise CommandError(f"Falha no upload: {type(e).__name__}: {e}")
