from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

# db_constraint=False: o modelo auth.User foi trocado por hackathon.User (AUTH_USER_MODEL), então a tabela
# auth_user não existe em bancos novos. Em PostgreSQL a FK falhava; o campo é removido na 0016.
class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('hackathon', '0010_merge_0009_equipe_0009_nota'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auth_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hackathon_user', to='auth.user', db_constraint=False)),
                ('tipoUser', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hackathon.tipouser')),
            ],
        ),
    ]
