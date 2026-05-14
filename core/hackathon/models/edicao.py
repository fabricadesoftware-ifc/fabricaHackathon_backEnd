
from django.db import models
from .tipo_edicao import TipoEdicao
from .apoiador import Apoiador
from django.core.exceptions import ValidationError

class Edicao(models.Model):
    
    STATUS_CHOICES = [
        ('INSCRICAO', 'Inscrição'),
        ('EM_ANDAMENTO', 'Em andamento'),
        ('AVALIACAO', 'Avaliação'),
        ('FINALIZADO', 'Finalizado')
    ]
    
    nome = models.CharField(null=False, blank=False, max_length=100)
    ano = models.PositiveIntegerField(null=False, blank=False)
    
    descricao = models.TextField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, blank=False, null=False, default='INSCRICAO', max_length=20)
    
    data_inicio = models.DateField(null=False, blank=False)
    data_fim = models.DateField(null=False, blank=False)
    
    minimo_participantes = models.PositiveIntegerField(null=False, blank=False)
    maximo_participantes = models.PositiveIntegerField(null=False, blank=False)
    maximo_equipes = models.PositiveIntegerField(null=False, blank=False)
    
    tipo_edicao = models.ForeignKey(TipoEdicao, on_delete=models.PROTECT, related_name="edicoes")
    apoiadores = models.ManyToManyField(Apoiador, related_name="edicoes", blank=True)

    class Meta:
        verbose_name_plural = "Edições"

    def __str__(self):
        return f"{self.nome} - {self.ano}"    