# Generated by Django 3.0.3 on 2020-02-11 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_referral', '0003_add_interaction_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='companyreferral',
            name='closure_reason',
            field=models.CharField(blank=True, choices=[('unreachable', 'The company or contact couldn’t be reached'), ('insufficient_information', 'The information in this referral is insufficient'), ('wrong_recipient', 'I’m not the right person for this referral')], max_length=255),
        ),
    ]