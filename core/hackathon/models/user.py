from django.db import models
from django.contrib.auth.models import AbstractUser
from ..validations.imagem_validation import validate_imagem

class tipoUser(models.TextChoices):
    participante = 'PARTICIPANTE', 'Participante'
    avaliador = 'AVALIADOR', 'Avaliador'
    professor = 'PROFESSOR', 'Professor'
    admin = 'ADMIN', 'Administrador'

class User(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)
    tipoUser = models.CharField(max_length=20, choices=tipoUser.choices, default=tipoUser.participante)
    foto_perfil = models.ImageField(upload_to='hackathon/usuarios/', null=True, blank=True, validators=[validate_imagem])

    class Meta(AbstractUser.Meta):
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        nome = self.get_full_name() or self.first_name or self.username
        return f"{nome} ({self.email})"