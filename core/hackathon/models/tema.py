from django.db import models
from .edicao import Edicao

class Tema(models.Model):
    descricao_tema = models.CharField(max_length=45, blank=False, null=False)
    edicao = models.ForeignKey(Edicao, on_delete=models.PROTECT, related_name="temas", blank=False, null=False)

    class Meta:
        verbose_name_plural = "Temas"
    def __str__(self):
        return f'{self.descricao_tema} - {self.edicao}'
    