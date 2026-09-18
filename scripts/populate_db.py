import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Add the parent directory to sys.path so we can import from 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from core.hackathon.models import (
    TipoEdicao, Apoiador, User, Edicao, Criterio, Tema, Projeto, Equipe, Nota, ParticipanteEquipe
)
from core.hackathon.models.user import tipoUser

def populate():
    print("Iniciando a população do banco de dados...")

    # 1. TipoEdicao
    print("Criando TipoEdicao...")
    tipo_presencial, _ = TipoEdicao.objects.get_or_create(nome='Presencial')
    tipo_online, _ = TipoEdicao.objects.get_or_create(nome='Online')
    tipo_hibrido, _ = TipoEdicao.objects.get_or_create(nome='Híbrido')

    # 2. Apoiador
    print("Criando Apoiadores...")
    apoiador1, _ = Apoiador.objects.get_or_create(nome='TechCorp', defaults={'tipo': 'ouro'})
    apoiador2, _ = Apoiador.objects.get_or_create(nome='DevStart', defaults={'tipo': 'prata'})
    apoiador3, _ = Apoiador.objects.get_or_create(nome='InovaBank', defaults={'tipo': 'diamante'})

    # 3. Edicao
    print("Criando Edicao...")
    edicao_2024, created = Edicao.objects.get_or_create(
        nome='Hackathon Inovação 2024',
        ano=2024,
        defaults={
            'descricao': 'O maior hackathon de inovação do ano.',
            'status': 'INSCRICAO',
            'data_inicio': date.today(),
            'data_fim': date.today() + timedelta(days=3),
            'minimo_participantes': 3,
            'maximo_participantes': 5,
            'maximo_equipes': 20,
            'tipo_edicao': tipo_hibrido
        }
    )
    if created:
        edicao_2024.apoiadores.add(apoiador1, apoiador3)

    # 4. Criterio
    print("Criando Criterios...")
    criterio_inovacao, _ = Criterio.objects.get_or_create(nome='Inovação', edicao=edicao_2024)
    criterio_usabilidade, _ = Criterio.objects.get_or_create(nome='Usabilidade', edicao=edicao_2024)
    criterio_impacto, _ = Criterio.objects.get_or_create(nome='Impacto Social', edicao=edicao_2024)

    # 5. Tema
    print("Criando Temas...")
    tema_saude, _ = Tema.objects.get_or_create(descricao_tema='Saúde e Bem-estar', edicao=edicao_2024)
    tema_educacao, _ = Tema.objects.get_or_create(descricao_tema='Educação do Futuro', edicao=edicao_2024)

    # 6. Users
    print("Criando Users...")
    user1, _ = User.objects.get_or_create(
        username='joao',
        defaults={
            'nome_user': 'João Silva',
            'email_user': 'joao@example.com',
            'email': 'joao@example.com',
            'tipoUser': tipoUser.participante
        }
    )
    if not user1.has_usable_password():
        user1.set_password('123456')
        user1.save()

    user2, _ = User.objects.get_or_create(
        username='maria',
        defaults={
            'nome_user': 'Maria Souza',
            'email_user': 'maria@example.com',
            'email': 'maria@example.com',
            'tipoUser': tipoUser.avaliador
        }
    )
    if not user2.has_usable_password():
        user2.set_password('123456')
        user2.save()

    user_admin, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'nome_user': 'Administrador',
            'email_user': 'admin@example.com',
            'email': 'admin@example.com',
            'tipoUser': tipoUser.admin,
            'is_staff': True,
            'is_superuser': True
        }
    )
    if not user_admin.has_usable_password():
        user_admin.set_password('123456')
        user_admin.save()

    # 7. Projeto
    print("Criando Projetos...")
    projeto_saude, _ = Projeto.objects.get_or_create(
        nome_projeto='App Vida Saudável',
        edicao=edicao_2024,
        defaults={
            'descricao_projeto': 'Um aplicativo para monitorar hábitos de saúde.',
            'link_deploy_projeto': 'https://vidasaudavel.example.com',
            'notaFinal_projeto': None
        }
    )

    projeto_edu, _ = Projeto.objects.get_or_create(
        nome_projeto='Plataforma Educar',
        edicao=edicao_2024,
        defaults={
            'descricao_projeto': 'Plataforma EAD para escolas públicas.',
            'link_deploy_projeto': 'https://educar.example.com',
            'notaFinal_projeto': None
        }
    )

    # 8. Equipe
    print("Criando Equipes...")
    equipe_alpha, _ = Equipe.objects.get_or_create(
        nome_equipe='Equipe Alpha',
        edicao=edicao_2024,
        defaults={
            'tema': tema_saude,
            'projeto': projeto_saude
        }
    )

    equipe_beta, _ = Equipe.objects.get_or_create(
        nome_equipe='Equipe Beta',
        edicao=edicao_2024,
        defaults={
            'tema': tema_educacao,
            'projeto': projeto_edu
        }
    )

    # 9. ParticipanteEquipe
    print("Associando Participantes às Equipes...")
    ParticipanteEquipe.objects.get_or_create(
        user=user1,
        equipe=equipe_alpha
    )

    # 10. Nota
    print("Criando Notas...")
    Nota.objects.get_or_create(
        projeto=projeto_saude,
        criterio=criterio_inovacao,
        defaults={'nota': Decimal('8.50'), 'comentario_nota': 'Boa ideia, mas pode melhorar.'}
    )
    Nota.objects.get_or_create(
        projeto=projeto_saude,
        criterio=criterio_usabilidade,
        defaults={'nota': Decimal('9.00'), 'comentario_nota': 'Interface muito bonita.'}
    )

    print("Banco de dados populado com sucesso!")

if __name__ == '__main__':
    populate()
