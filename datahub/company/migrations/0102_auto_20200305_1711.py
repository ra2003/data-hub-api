# Generated by Django 3.0.3 on 2020-03-05 17:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0101_companyexportcountryhistory'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='company',
            options={'permissions': (('view_company_document', 'Can view company document'), ('view_company_timeline', 'Can view company timeline'), ('export_company', 'Can export company'), ('change_regional_account_manager', 'Can change regional account manager'), ('view_export_win', 'Can view company export win')), 'verbose_name_plural': 'companies'},
        ),
    ]
