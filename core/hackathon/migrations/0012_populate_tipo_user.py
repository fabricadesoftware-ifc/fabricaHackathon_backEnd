from django.db import migrations

def populate_tipo_user(apps, schema_editor):
    TipoUser = apps.get_model('hackathon', 'TipoUser')
    tipos = ['Participante', 'Avaliador', 'Admin']
    for tipo in tipos:
        TipoUser.objects.get_or_create(nome=tipo)

def reverse_populate_tipo_user(apps, schema_editor):
    TipoUser = apps.get_model('hackathon', 'TipoUser')
    TipoUser.objects.filter(nome__in=['Participante', 'Avaliador', 'Admin']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('hackathon', '0011_user'),
    ]

    operations = [
        migrations.RunPython(populate_tipo_user, reverse_populate_tipo_user),
    ]
