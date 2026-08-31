from django.db import models
from django.core.exceptions import ValidationError
from .edicao import Edicao
from .projeto import Projeto
from .tema import Tema

class Equipe(models.Model):
    nome_equipe = models.CharField(null=False, blank=False, max_length=50)
    edicao = models.ForeignKey(Edicao, on_delete=models.PROTECT, related_name='equipes',blank=False, null=False)
    tema = models.ForeignKey(Tema, on_delete=models.PROTECT, related_name="equipes", blank=False, null=False)
    projeto = models.OneToOneField(Projeto, on_delete=models.PROTECT, related_name="equipes", blank=False, null=False)
    
    def clean(self):
        if self.pk and self.edicao_id:
            num_participantes = self.participantes.count()
            if num_participantes > self.edicao.maximo_participantes:
                raise ValidationError(f"A equipe já possui {num_participantes} participantes, excedendo o limite de {self.edicao.maximo_participantes} da edição.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome_equipe

    class Meta:
        verbose_name_plural = "Equipes"
        unique_together = ('nome_equipe', 'edicao')