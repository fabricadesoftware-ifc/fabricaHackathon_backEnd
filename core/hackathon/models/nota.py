from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .avaliadorEdicao import AvaliadorEdicao

class Nota(models.Model):
    nota = models.DecimalField(
    max_digits=4,
    decimal_places=2,
    validators=[
        MinValueValidator(0),
        MaxValueValidator(10)
    ]
)
    comentario_nota = models.TextField(blank=True, null=True )
    projeto = models.ForeignKey('Projeto', on_delete=models.CASCADE, related_name="notas", blank=False, null=False)
    criterio = models.ForeignKey('Criterio', on_delete=models.CASCADE, related_name="notas", blank=False, null=False)
    avaliador = models.ForeignKey('AvaliadorEdicao', on_delete=models.PROTECT, related_name="notas", blank=False, null=False)

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        unique_together = ('projeto', 'criterio', 'avaliador')