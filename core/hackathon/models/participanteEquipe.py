from django.db import models
from django.core.exceptions import ValidationError
from .user import User, tipoUser
from .equipe import Equipe

class ParticipanteEquipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="equipes", blank=False, null=False)
    equipe = models.ForeignKey(Equipe, on_delete=models.PROTECT, related_name="participantes", blank=False, null=False)

    def clean(self):
        if self.user_id and self.user.tipoUser != tipoUser.participante:
            raise ValidationError({"user": "Apenas usuários com perfil de Participante podem fazer parte de uma equipe."})

        if self.user_id and self.equipe_id:
            qs = ParticipanteEquipe.objects.filter(
                user_id=self.user_id,
                equipe__edicao_id=self.equipe.edicao_id
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            equipe_existente = qs.select_related('equipe').first()
            if equipe_existente:
                raise ValidationError({
                    "user": f"O usuário já faz parte da equipe '{equipe_existente.equipe.nome_equipe}' nesta mesma edição."
                })

        if self.equipe_id:
            num_participantes = self.equipe.participantes.exclude(pk=self.pk).count()
            if num_participantes >= self.equipe.edicao.maximo_participantes:
                raise ValidationError(f"A equipe já atingiu o limite máximo de {self.equipe.edicao.maximo_participantes} participantes.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} - {self.equipe}'

    class Meta:
        verbose_name_plural = "Participantes Equipe"
        unique_together = ('user', 'equipe')