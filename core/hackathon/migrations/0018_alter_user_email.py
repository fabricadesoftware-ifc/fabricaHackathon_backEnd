from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hackathon', '0017_alter_user_date_joined_alter_user_email_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
