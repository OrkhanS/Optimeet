# Generated by Django 2.2.8 on 2020-04-29 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('APP', '0002_auto_20200416_1531'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='wantstoMatch',
            field=models.BooleanField(default=True, verbose_name='does user want to Match someone?'),
        ),
    ]
