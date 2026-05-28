from django.db import models
from .edicao import Edicao

class Criterio(models.Model):
    nome = models.CharField( null=False, blank=False, max_length=50)
    edicao = models.ForeignKey(Edicao, on_delete=models.PROTECT, related_name="criterios")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = "Critérios"
