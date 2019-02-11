# Generated by Django 2.1.4 on 2019-02-04 14:28

from pathlib import PurePath

from django.conf import settings
from django.db import migrations, models
from datahub.core.migration_utils import load_yaml_data_in_migration
import uuid


def load_activity_types(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0056_activity_type.yaml',
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reversion', '0001_squashed_0004_auto_20160611_1202'),
        ('investment', '0055_project_manager_request_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvestmentActivity',
            fields=[
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('text', models.TextField()),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('investment_project', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='activities', to='investment.InvestmentProject')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_on',),
            },
        ),
        migrations.CreateModel(
            name='InvestmentActivityType',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='investmentactivity',
            name='activity_type',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, related_name='+', to='investment.InvestmentActivityType'),
        ),
        migrations.AddField(
            model_name='investmentactivity',
            name='revision',
            field=models.OneToOneField(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='reversion.Revision'),
        ),
        migrations.RunPython(load_activity_types, migrations.RunPython.noop),
    ]
