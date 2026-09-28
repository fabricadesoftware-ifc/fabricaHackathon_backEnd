from django.db import models
from .edicao import Edicao
from .tema import Tema

class Projeto(models.Model):
    nome_projeto = models.CharField(max_length=100, blank=False, null=False)
    descricao_projeto = models.TextField(blank=False, null=False)
    link_deploy_projeto = models.URLField(blank=True, null=True)
    notaFinal_projeto = models.DecimalField(
    max_digits=4,
    decimal_places=2,
    validators=[
        MinValueValidator(0),
        MaxValueValidator(10)
    ]
)
    edicao = models.ForeignKey(Edicao, on_delete=models.PROTECT, related_name="projetos", blank=False, null=False)

    def __str__(self):
        return f'{self.nome_projeto} - {self.link_deploy_projeto}'

    class Meta:
        verbose_name_plural = "Projetos"
