from django.db import models
from django.contrib.auth.models import AbstractUser

class tipoUser(models.TextChoices):
    participante = 'PARTICIPANTE', 'Participante'
    avaliador = 'AVALIADOR', 'Avaliador'
    admin = 'ADMIN', 'Administrador'

class User(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)
    tipoUser = models.CharField(max_length=20, choices=tipoUser.choices, default=tipoUser.participante)

    class Meta(AbstractUser.Meta):
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        nome = self.get_full_name() or self.first_name or self.username
        return f"{nome} ({self.email})"