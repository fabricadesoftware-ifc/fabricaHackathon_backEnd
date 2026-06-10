from django.db import models
from .edicao import Edicao
from .projeto import Projeto
from .tema import Tema
class Equipes(models.Model):
    nome_equipe = models.CharField(null=False, blank=False, max_length=50)
    edicao = models.ForeignKey(Edicao, on_delete=models.PROTECT, related_name='equipes',blank=False, null=False)
    tema = models.ForeignKey(Tema, on_delete=models.PROTECT, related_name="equipes", blank=False, null=False)
    projeto = models.ForeignKey(Projeto, on_delete=models.PROTECT, related_name="equipes", blank=False, null=False)
    
    def __str__(self):
        return self.nome_equipe

    class Meta:
        verbose_name_plural = "Equipes"