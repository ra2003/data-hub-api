# Generated by Django 2.0.4 on 2018-05-15 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0042_correct_spi_stage_log_created_on_and_ordering'),
    ]

    operations = [
        migrations.AddField(
            model_name='investmentproject',
            name='project_manager_first_assigned_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]