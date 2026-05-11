from django.db import models

class Apoiador(models.Model):
    TIPO_CHOICES = [
        ('prata', 'Prata'),
        ('ouro', 'Ouro'),
        ('diamante', 'Diamante'),
    ]
    nome = models.CharField(null=True, blank=False, unique=True)
    tipo = models.CharField(choices=TIPO_CHOICES, blank=False, default=TIPO_CHOICES[0])

    class Meta:
        verbose_name_plural = "Apoiadores"