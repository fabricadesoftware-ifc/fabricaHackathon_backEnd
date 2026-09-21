from django.db import models
from django.core.exceptions import ValidationError
from .user import User, tipoUser
from .edicao import Edicao


class AvaliadorEdicao(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="edicoes_avaliador",
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
        if self.user_id and self.user.tipoUser != tipoUser.avaliador:
            raise ValidationError({
                "user": "Apenas usuários com perfil de Avaliador podem ser vinculados a uma edição."
            })

        if self.user_id and self.edicao_id:
            qs = AvaliadorEdicao.objects.filter(
                user_id=self.user_id,
                edicao_id=self.edicao_id
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    "user": "Este usuário já está vinculado como avaliador nesta edição."
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.edicao}"

    class Meta:
        verbose_name = "Avaliador da Edição"
        verbose_name_plural = "Avaliadores da Edição"
        unique_together = ('user', 'edicao')


Avaliador = AvaliadorEdicao