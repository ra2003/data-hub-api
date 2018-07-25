# Generated by Django 2.0.4 on 2018-05-14 10:43
from pathlib import PurePath

from django.core.management import call_command
from django.db import migrations
from django.db.migrations import RunPython


def load_investment_spi_services(apps, schema_editor):
    call_command(
        'loaddata',
        PurePath(__file__).parent / '0012_investment_spi_service_aftercare_offered.yaml'
    )

class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0011_add_team_tags'),
    ]

    operations = [
        RunPython(load_investment_spi_services, RunPython.noop),
    ]