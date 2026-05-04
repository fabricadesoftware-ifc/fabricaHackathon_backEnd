from django.db import models

class TipoEdicao(models.Model):
    nome = models.CharField(unique=True, null=False, blank=False, max_length=100)
    def __str__(self):
        return self.nome