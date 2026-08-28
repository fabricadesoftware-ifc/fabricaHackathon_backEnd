from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hackathon', '0010_merge_0009_equipe_0009_nota'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_user', models.CharField(max_length=255)),
                ('email_user', models.EmailField(max_length=254, unique=True)),
                ('auth_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hackathon_user', to=settings.AUTH_USER_MODEL)),
                ('tipoUser', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hackathon.tipouser')),
            ],
        ),
    ]
