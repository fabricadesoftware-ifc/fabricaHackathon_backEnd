import secrets

from django.db import models

from .equipe import Equipe


def gerar_token():
    return secrets.token_urlsafe(24)


class ConviteEquipe(models.Model):
    """Link de convite da equipe: reutilizável por qualquer pessoa com conta até lotar; o criador pode desativar."""

    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name="convites")
    token = models.CharField(max_length=64, unique=True, default=gerar_token, editable=False)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"link de {self.equipe} ({'ativo' if self.ativo else 'desativado'})"

    class Meta:
        verbose_name_plural = "Convites de equipe"
        ordering = ["id"]
