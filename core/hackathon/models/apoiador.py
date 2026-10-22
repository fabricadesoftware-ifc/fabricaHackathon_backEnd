from django.db import models
from ..validations.imagem_validation import validate_imagem

class Apoiador(models.Model):
    TIPO_CHOICES = [
        ('prata', 'Prata'),
        ('ouro', 'Ouro'),
        ('diamante', 'Diamante'),
    ]
    nome = models.CharField(max_length=100, null=True, blank=False, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, blank=False, default=TIPO_CHOICES[0])
    logo_apoiador = models.ImageField(upload_to='hackathon/apoiadores/', null=True, blank=True, validators=[validate_imagem])

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = "Apoiadores"