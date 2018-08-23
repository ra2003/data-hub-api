from datahub.company.models import Company as DBCompany
from .models import Company
from .views import SearchCompanyAPIView
from ..apps import SearchApp


class CompanySearchApp(SearchApp):
    """SearchApp for company."""

    name = 'company'
    es_model = Company
    view = SearchCompanyAPIView
    view_permissions = ('company.view_company',)
    queryset = DBCompany.objects.select_related(
        'account_manager',
        'archived_by',
        'business_type',
        'classification',
        'employee_range',
        'export_experience_category',
        'headquarter_type',
        'one_list_account_owner',
        'global_headquarters',
        'registered_address_country',
        'sector',
        'sector__parent',
        'sector__parent__parent',
        'trading_address_country',
        'turnover_range',
        'uk_region',
    )
