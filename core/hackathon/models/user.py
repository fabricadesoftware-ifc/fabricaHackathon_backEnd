from django.db import models
from django.contrib.auth.models import User as AuthUser
from .tipo_user import TipoUser

class User(models.Model):
    auth_user = models.OneToOneField(AuthUser, on_delete=models.CASCADE, related_name='hackathon_user')
    nome_user = models.CharField(max_length=255, null=False, blank=False)
    email_user = models.EmailField(unique=True, null=False, blank=False)
    tipoUser = models.ForeignKey(TipoUser, on_delete=models.PROTECT, null=False, blank=False)

    def __str__(self):
        return f"{self.nome_user} ({self.email_user})"
