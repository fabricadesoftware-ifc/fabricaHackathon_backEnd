from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .edicao import Edicao
from .tema import Tema
from ..validations.imagem_validation import validate_imagem

class Projeto(models.Model):
    nome_projeto = models.CharField(max_length=100, blank=False, null=False)
    descricao_projeto = models.TextField(blank=True, default="")
    link_deploy_projeto = models.URLField(blank=True, null=True)
    notaFinal_projeto = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10)
        ]
    )
    logo_projeto = models.ImageField(upload_to='hackathon/projetos/', null=True, blank=True, validators=[validate_imagem])
    edicao = models.ForeignKey(Edicao, on_delete=models.PROTECT, related_name="projetos", blank=False, null=False)

    def __str__(self):
        return f'{self.nome_projeto} - {self.link_deploy_projeto}'

    class Meta:
        verbose_name_plural = "Projetos"
