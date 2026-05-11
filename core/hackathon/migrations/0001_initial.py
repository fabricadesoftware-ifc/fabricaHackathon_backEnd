from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Apoiador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(null=True)),
                ('tipo', models.CharField(
                    choices=[
                        ('prata', 'Prata'),
                        ('ouro', 'Ouro'),
                        ('diamante', 'Diamante')
                    ]
                )),
            ],
        ),

        migrations.CreateModel(
            name='TipoEdicao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, unique=True)),
            ],
        ),
    ]