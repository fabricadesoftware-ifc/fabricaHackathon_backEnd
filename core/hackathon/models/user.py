from django.db import models
from django.contrib.auth.models import User as AuthUser

class tipoUser (models.TextChoices):
    participante = 'PARTICIPANTE', 'Participante'
    avaliador = 'AVALIADOR', 'Avaliador'
    admin = 'ADMIN', 'Administrador'

class User(models.Model):
    auth_user = models.OneToOneField(AuthUser, on_delete=models.PROTECT, related_name='hackathon_user')
    nome_user = models.CharField(max_length=255, null=False, blank=False)
    email_user = models.EmailField(unique=True, null=False, blank=False)
    tipoUser = models.CharField(max_length=20, choices=tipoUser.choices, default=tipoUser.participante)
    
    def __str__(self):
        return f"{self.nome_user} ({self.email_user})"