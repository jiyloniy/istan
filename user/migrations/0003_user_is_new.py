# Generated by Django 5.1.3 on 2025-05-12 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_alter_user_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_new',
            field=models.BooleanField(default=True),
        ),
    ]
