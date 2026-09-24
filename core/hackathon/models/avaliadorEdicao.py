from django.db import models
from django.core.exceptions import ValidationError
from .user import User, tipoUser
from .edicao import Edicao


class AvaliadorEdicao(models.Model):
    avaliador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="edicoes_avaliadas",
        blank=False,
        null=False
    )
    edicao = models.ForeignKey(
        Edicao,
        on_delete=models.PROTECT,
        related_name="avaliadores",
        blank=False,
        null=False
    )

    def clean(self):
        if self.avaliador_id and self.avaliador.tipoUser != tipoUser.avaliador:
            raise ValidationError({
                "avaliador": "Apenas usuários com perfil de Avaliador podem ser vinculados a uma edição."
            })

        if self.avaliador_id and self.edicao_id:
            qs = AvaliadorEdicao.objects.filter(
                avaliador_id=self.avaliador_id,
                edicao_id=self.edicao_id
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    "avaliador": "Este usuário já está vinculado como avaliador nesta edição."
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.avaliador.get_full_name() or self.avaliador.username} - {self.edicao.nome}"

    class Meta:
        verbose_name = "Avaliador da Edição"
        verbose_name_plural = "Avaliadores por Edição"
        unique_together = ('avaliador', 'edicao')


Avaliador = AvaliadorEdicao