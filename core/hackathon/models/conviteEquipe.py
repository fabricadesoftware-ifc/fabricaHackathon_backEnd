import secrets

from django.db import models

from .equipe import Equipe
from .user import User


def gerar_token():
    return secrets.token_urlsafe(24)


class ConviteEquipe(models.Model):
    """
    Convite para entrar numa equipe. Dois formatos:
    - por e-mail (`email` preenchido): vale para uma pessoa, vira ACEITO quando ela entra;
    - link da equipe (`email` vazio): reutilizável por qualquer pessoa com conta até lotar; fica sempre PENDENTE
      até ser revogado (CANCELADO).
    """

    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Convite enviado"
        ACEITO = "ACEITO", "Aceito"
        CANCELADO = "CANCELADO", "Cancelado"

    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name="convites")
    email = models.EmailField(blank=True, default="")
    token = models.CharField(max_length=64, unique=True, default=gerar_token, editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    email_enviado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    aceito_em = models.DateTimeField(null=True, blank=True)
    aceito_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    @property
    def eh_link(self):
        return not self.email

    def __str__(self):
        return f"{self.email or 'link'} → {self.equipe} ({self.status})"

    class Meta:
        verbose_name_plural = "Convites de equipe"
        ordering = ["id"]
