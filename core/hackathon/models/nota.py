from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

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
    