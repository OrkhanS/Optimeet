# Generated by Django 2.2.8 on 2020-04-10 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('APP', '0003_auto_20200410_1037'),
    ]

    operations = [
        migrations.AddField(
            model_name='roommembers',
            name='userAccess',
            field=models.BooleanField(default=True, verbose_name='Can user Access to Room'),
        ),
        migrations.AddField(
            model_name='user',
            name='hasMatchedToday',
            field=models.BooleanField(default=False, verbose_name='Has user matched today'),
        ),
    ]