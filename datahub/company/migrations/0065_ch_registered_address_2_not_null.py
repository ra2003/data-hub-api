# Generated by Django 2.1.5 on 2019-02-12 16:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0064_make_registered_address_blank'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companieshousecompany',
            name='registered_address_2',
            field=models.CharField(blank=True, default='', max_length=255),
            preserve_default=False,
        ),
    ]
