from django.db import models, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .user import User, tipoUser


class SolicitacaoPerfil(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        APROVADA = 'APROVADA', 'Aprovada'
        RECUSADA = 'RECUSADA', 'Recusada'

    PERFIS_SOLICITAVEIS = [
        (tipoUser.avaliador.value, tipoUser.avaliador.label),
        (tipoUser.professor.value, tipoUser.professor.label),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitacoes_perfil')
    perfil_solicitado = models.CharField(max_length=20, choices=PERFIS_SOLICITAVEIS)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    criada_em = models.DateTimeField(auto_now_add=True)
    decidida_em = models.DateTimeField(null=True, blank=True)
    decidida_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitacoes_decididas'
    )

    class Meta:
        verbose_name = 'Solicitação de perfil'
        verbose_name_plural = 'Solicitações de perfil'
        ordering = ['-criada_em', '-id']

    def __str__(self):
        return f'{self.usuario} → {self.perfil_solicitado} ({self.status})'

    def _decidir(self, status, decidida_por):
        if self.status != self.Status.PENDENTE:
            raise ValidationError({'status': 'Esta solicitação já foi decidida.'})
        self.status = status
        self.decidida_em = timezone.now()
        self.decidida_por = decidida_por
        self.save(update_fields=['status', 'decidida_em', 'decidida_por'])

    @transaction.atomic
    def aprovar(self, decidida_por):
        self._decidir(self.Status.APROVADA, decidida_por)
        self.usuario.tipoUser = self.perfil_solicitado
        self.usuario.save(update_fields=['tipoUser'])

    @transaction.atomic
    def recusar(self, decidida_por):
        self._decidir(self.Status.RECUSADA, decidida_por)
