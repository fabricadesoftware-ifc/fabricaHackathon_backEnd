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

from django.contrib.auth.models import User as AuthUser
from core.hackathon.models import (
    TipoEdicao, Apoiador, TipoUser, User, Edicao, Criterio, Tema, Projeto, Equipe, Nota
)

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

    # 3. TipoUser
    print("Criando TipoUser...")
    tipo_participante, _ = TipoUser.objects.get_or_create(nome='Participante')
    tipo_avaliador, _ = TipoUser.objects.get_or_create(nome='Avaliador')
    tipo_organizador, _ = TipoUser.objects.get_or_create(nome='Organizador')

    # 4. Edicao
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

    # 5. Criterio
    print("Criando Criterios...")
    criterio_inovacao, _ = Criterio.objects.get_or_create(nome='Inovação', edicao=edicao_2024)
    criterio_usabilidade, _ = Criterio.objects.get_or_create(nome='Usabilidade', edicao=edicao_2024)
    criterio_impacto, _ = Criterio.objects.get_or_create(nome='Impacto Social', edicao=edicao_2024)

    # 6. Tema
    print("Criando Temas...")
    tema_saude, _ = Tema.objects.get_or_create(descricao_tema='Saúde e Bem-estar', edicao=edicao_2024)
    tema_educacao, _ = Tema.objects.get_or_create(descricao_tema='Educação do Futuro', edicao=edicao_2024)

    # 7. Users
    print("Criando Users...")
    auth_user1, _ = AuthUser.objects.get_or_create(username='joao', defaults={'email': 'joao@example.com'})
    if not auth_user1.has_usable_password():
        auth_user1.set_password('123456')
        auth_user1.save()
        
    user1, _ = User.objects.get_or_create(
        auth_user=auth_user1,
        defaults={'nome_user': 'João Silva', 'email_user': 'joao@example.com', 'tipoUser': tipo_participante}
    )

    auth_user2, _ = AuthUser.objects.get_or_create(username='maria', defaults={'email': 'maria@example.com'})
    if not auth_user2.has_usable_password():
        auth_user2.set_password('123456')
        auth_user2.save()
        
    user2, _ = User.objects.get_or_create(
        auth_user=auth_user2,
        defaults={'nome_user': 'Maria Souza', 'email_user': 'maria@example.com', 'tipoUser': tipo_avaliador}
    )

    # 8. Projeto
    print("Criando Projetos...")
    projeto_saude, _ = Projeto.objects.get_or_create(
        nome_projeto='App Vida Saudável',
        edicao=edicao_2024,
        tema=tema_saude,
        defaults={
            'descricao_projeto': 'Um aplicativo para monitorar hábitos de saúde.',
            'link_deploy_projeto': 'https://vidasaudavel.example.com',
            'notaFinal_projeto': None
        }
    )

    projeto_edu, _ = Projeto.objects.get_or_create(
        nome_projeto='Plataforma Educar',
        edicao=edicao_2024,
        tema=tema_educacao,
        defaults={
            'descricao_projeto': 'Plataforma EAD para escolas públicas.',
            'link_deploy_projeto': 'https://educar.example.com',
            'notaFinal_projeto': None
        }
    )

    # 9. Equipe
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
