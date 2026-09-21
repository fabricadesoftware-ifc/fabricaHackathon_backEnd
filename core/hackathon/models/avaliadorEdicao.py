from django.db import models
from .edicao import Edicao
from .user import User


class AvaliadorEdicao(models.Model):
    edicao = models.ForeignKey(Edicao, on_delete=models.PROTECT, related_name="avaliadores")
    avaliador = models.ForeignKey(User, on_delete=models.PROTECT, related_name="edicoes_avaliadas")

    def __str__(self):
        return f"{self.avaliador.get_full_name()} - {self.edicao.nome}"

    class Meta:
        verbose_name_plural = "Avaliadores por Edição"