from django.db import models
from django.contrib.auth.models import AbstractUser

class tipoUser (models.TextChoices):
    participante = 'PARTICIPANTE', 'Participante'
    avaliador = 'AVALIADOR', 'Avaliador'
    admin = 'ADMIN', 'Administrador'

class User(AbstractUser):
    nome_user = models.CharField(max_length=255, null=False, blank=False)
    email_user = models.EmailField(unique=True, null=False, blank=False)
    tipoUser = models.CharField(max_length=20, choices=tipoUser.choices, default=tipoUser.participante)

    class Meta(AbstractUser.Meta):
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def save(self, *args, **kwargs):
        if not self.email and self.email_user:
            self.email = self.email_user
        if not self.first_name and self.nome_user:
            self.first_name = self.nome_user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome_user} ({self.email_user})"