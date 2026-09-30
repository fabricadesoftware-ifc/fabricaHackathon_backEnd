from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
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
    comentario_nota = models.TextField(blank=True, null=True)
    projeto = models.ForeignKey('Projeto', on_delete=models.PROTECT, related_name="notas", blank=False, null=False)
    criterio = models.ForeignKey('Criterio', on_delete=models.PROTECT, related_name="notas", blank=False, null=False)
    avaliador = models.ForeignKey('AvaliadorEdicao', on_delete=models.PROTECT, related_name="notas", blank=False, null=False)

    def clean(self):
        errors = {}
        if self.avaliador_id and self.projeto_id:
            if self.avaliador.edicao_id != self.projeto.edicao_id:
                errors['avaliador'] = "O avaliador não pertence à mesma edição do projeto avaliado."

        if self.criterio_id and self.projeto_id:
            if self.criterio.edicao_id != self.projeto.edicao_id:
                errors['criterio'] = "O critério não pertence à mesma edição do projeto avaliado."

        if self.avaliador_id and self.projeto_id and self.criterio_id:
            qs = Nota.objects.filter(
                avaliador_id=self.avaliador_id,
                projeto_id=self.projeto_id,
                criterio_id=self.criterio_id
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['__all__'] = "Este critério já foi avaliado por este avaliador para este projeto."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.projeto} - {self.criterio}: {self.nota}"

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        unique_together = ('projeto', 'criterio', 'avaliador')