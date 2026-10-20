from django.core.files.storage import storages
from django.db import models

from ..validations.documento_validation import validate_documento
from .projeto import Projeto


def storage_documentos():
    return storages["documentos"]


class PreAvaliacao(models.Model):
    """Formulário preenchido pela equipe; vale 10% da nota final do projeto."""

    class Organizacao(models.TextChoices):
        KANBAN = "KANBAN", "Kanban"
        LISTA = "LISTA", "Lista de tarefas"
        CONVERSA = "CONVERSA", "Só conversa"
        OUTRO = "OUTRO", "Outro"

    class Hospedagem(models.TextChoices):
        FABROKU = "FABROKU", "Fabroku"
        OUTRA = "OUTRA", "Outra plataforma"
        LOCAL = "LOCAL", "Local"

    class Banco(models.TextChoices):
        FABROKU_POSTGRES = "FABROKU_POSTGRES", "PostgreSQL do Fabroku"
        SUPABASE = "SUPABASE", "Supabase"
        NEON = "NEON", "Neon"
        RENDER = "RENDER", "Render"
        OUTRO = "OUTRO", "Outro serviço"
        LOCAL = "LOCAL", "Local"

    projeto = models.OneToOneField(Projeto, on_delete=models.CASCADE, related_name="pre_avaliacao")

    # Seção 1: equipe e organização
    responsabilidades = models.JSONField(default=list, blank=True)  # [{"user": id, "area": "back"}]
    organizacao_metodo = models.CharField(max_length=20, choices=Organizacao.choices, blank=True)
    organizacao_link = models.URLField(blank=True)

    # Seção 2: entendimento do problema
    problema_entendido = models.TextField(blank=True)
    problema_explicacao = models.TextField(blank=True)
    maior_dificuldade = models.TextField(blank=True)
    proximos_passos = models.TextField(blank=True)

    # Seção 3: arquivos de arquitetura
    arquivo_rfs_rnfs = models.FileField(
        upload_to="hackathon/pre-avaliacao/", storage=storage_documentos,
        null=True, blank=True, validators=[validate_documento],
    )
    arquitetura_arquivo = models.FileField(
        upload_to="hackathon/pre-avaliacao/", storage=storage_documentos,
        null=True, blank=True, validators=[validate_documento],
    )
    arquitetura_link = models.URLField(blank=True)

    # Seção 4: aplicação hospedada
    hospedagem_plataforma = models.CharField(max_length=20, choices=Hospedagem.choices, blank=True)
    hospedagem_link = models.URLField(blank=True)
    hospedagem_justificativa = models.TextField(blank=True)

    # Seção 5: banco de dados
    banco_plataforma = models.CharField(max_length=20, choices=Banco.choices, blank=True)
    banco_justificativa = models.TextField(blank=True)

    # Resultado (calculado automaticamente a cada gravação)
    nota = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    detalhe_pontuacao = models.JSONField(default=dict, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pré-avaliação"
        verbose_name_plural = "Pré-avaliações"

    def __str__(self):
        return f"Pré-avaliação de {self.projeto} ({self.nota})"
