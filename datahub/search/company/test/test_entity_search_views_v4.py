import uuid
from cgi import parse_header
from csv import DictReader
from io import StringIO
from unittest import mock
from uuid import UUID, uuid4

import factory
import pytest
from django.conf import settings
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.exceptions import DataHubException
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_csv_data,
    get_attr_or_none,
    random_obj_for_queryset,
)
from datahub.metadata.models import Sector
from datahub.metadata.test.factories import TeamFactory
from datahub.search.company.models import get_suggestions
from datahub.search.company.views import SearchCompanyExportAPIView

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data(setup_es):
    """Sets up data for the tests."""
    country_uk = constants.Country.united_kingdom.value.id
    country_us = constants.Country.united_states.value.id
    country_anguilla = constants.Country.anguilla.value.id
    uk_region = constants.UKRegion.south_east.value.id
    CompanyFactory(
        name='abc defg ltd',
        trading_names=['helm', 'nop'],
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_uk,
        registered_address_country_id=country_uk,
        address_country_id=country_uk,
        uk_region_id=uk_region,
    )
    CompanyFactory(
        name='abc defg us ltd',
        trading_names=['helm', 'nop', 'qrs'],
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_us,
        registered_address_country_id=country_us,
        address_country_id=country_us,
    )
    CompanyFactory(
        name='archived',
        trading_names=[],
        trading_address_1='Main Lane',
        trading_address_town='Somewhere',
        trading_address_country_id=country_anguilla,
        registered_address_country_id=country_anguilla,
        address_country_id=country_anguilla,
        archived=True,
    )
    setup_es.indices.refresh()


@pytest.fixture
def setup_headquarters_data(setup_es):
    """Sets up data for headquarter type tests."""
    CompanyFactory(
        name='ghq',
        headquarter_type_id=constants.HeadquarterType.ghq.value.id,
    )
    CompanyFactory(
        name='ehq',
        headquarter_type_id=constants.HeadquarterType.ehq.value.id,
    )
    CompanyFactory(
        name='ukhq',
        headquarter_type_id=constants.HeadquarterType.ukhq.value.id,
    )
    CompanyFactory(
        name='none',
        headquarter_type_id=None,
    )
    setup_es.indices.refresh()


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_company_search_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:search:company')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_response_body(self, setup_es):
        """Tests the response body of a search query."""
        company = CompanyFactory(
            company_number='123',
            trading_names=['Xyz trading', 'Abc trading'],
            global_headquarters=None,
            one_list_tier=None,
            one_list_account_owner=None,
        )
        setup_es.indices.refresh()

        url = reverse('api-v4:search:company')
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'count': 1,
            'results': [
                {
                    'id': str(company.pk),
                    'created_on': company.created_on.isoformat(),
                    'modified_on': company.modified_on.isoformat(),
                    'name': company.name,
                    'reference_code': company.reference_code,
                    'company_number': company.company_number,
                    'vat_number': company.vat_number,
                    'duns_number': company.duns_number,
                    'trading_names': company.trading_names,
                    'address': {
                        'line_1': company.address_1,
                        'line_2': company.address_2 or '',
                        'town': company.address_town,
                        'county': company.address_county or '',
                        'postcode': company.address_postcode or '',
                        'country': {
                            'id': str(company.trading_address_country.id),
                            'name': company.trading_address_country.name,
                        },
                    },
                    'registered_address': {
                        'line_1': company.registered_address_1,
                        'line_2': company.registered_address_2 or '',
                        'town': company.registered_address_town,
                        'county': company.registered_address_county or '',
                        'postcode': company.registered_address_postcode or '',
                        'country': {
                            'id': str(company.registered_address_country.id),
                            'name': company.registered_address_country.name,
                        },
                    },
                    'uk_based': (
                        company.address_country.id == uuid.UUID(
                            constants.Country.united_kingdom.value.id,
                        )
                    ),
                    'uk_region': {
                        'id': str(company.uk_region.id),
                        'name': company.uk_region.name,
                    },
                    'business_type': {
                        'id': str(company.business_type.id),
                        'name': company.business_type.name,
                    },
                    'contacts': [],
                    'description': company.description,
                    'employee_range': {
                        'id': str(company.employee_range.id),
                        'name': company.employee_range.name,
                    },
                    'export_experience_category': {
                        'id': str(company.export_experience_category.id),
                        'name': company.export_experience_category.name,
                    },
                    'export_to_countries': [],
                    'future_interest_countries': [],
                    'headquarter_type': company.headquarter_type,
                    'sector': {
                        'id': str(company.sector.id),
                        'name': company.sector.name,
                        'ancestors': [
                            {'id': str(ancestor.id)}
                            for ancestor in company.sector.get_ancestors()
                        ],
                    },
                    'turnover_range': {
                        'id': str(company.turnover_range.id),
                        'name': company.turnover_range.name,
                    },
                    'website': company.website,
                    'global_headquarters': None,
                    'archived': False,
                    'archived_by': None,
                    'archived_on': None,
                    'archived_reason': None,
                    'suggest': get_suggestions(company),
                },
            ],
        }

    @pytest.mark.parametrize(
        'filters,expected_companies',
        (
            # no filter
            (
                {},
                ['abc defg ltd', 'abc defg us ltd', 'archived'],
            ),

            # archived True
            (
                {
                    'archived': True,
                },
                ['archived'],
            ),

            # archived False
            (
                {
                    'archived': False,
                },
                ['abc defg ltd', 'abc defg us ltd'],
            ),

            # trading_address_country
            (
                {
                    'trading_address_country': constants.Country.united_states.value.id,
                },
                ['abc defg us ltd'],
            ),

            # multiple trading_address_country filters
            (
                {
                    'trading_address_country': [
                        constants.Country.united_states.value.id,
                        constants.Country.united_kingdom.value.id,
                    ],
                },
                ['abc defg ltd', 'abc defg us ltd'],
            ),

            # uk_region
            (
                {
                    'uk_region': constants.UKRegion.south_east.value.id,
                },
                ['abc defg ltd'],
            ),

            # uk_region
            (
                {
                    'uk_based': True,
                },
                ['abc defg ltd'],
            ),
        ),
    )
    def test_filters(self, setup_data, filters, expected_companies):
        """Tests different filters."""
        url = reverse('api-v4:search:company')

        response = self.api_client.post(
            url,
            data={
                **filters,
                'sortby': 'name',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(expected_companies)

        assert [
            result['name']
            for result in response_data['results']
        ] == expected_companies

    @pytest.mark.parametrize(
        'query,results',
        (
            (
                {
                    'headquarter_type': None,
                },
                {'none'},
            ),
            (
                {
                    'headquarter_type': constants.HeadquarterType.ghq.value.id,
                },
                {'ghq'},
            ),
            (
                {
                    'headquarter_type': [
                        constants.HeadquarterType.ghq.value.id,
                        constants.HeadquarterType.ehq.value.id,
                    ],
                },
                {'ehq', 'ghq'},
            ),
            (
                {
                    'headquarter_type': [
                        constants.HeadquarterType.ghq.value.id,
                        constants.HeadquarterType.ehq.value.id,
                        None,
                    ],
                },
                {'ehq', 'ghq', 'none'},
            ),
        ),
    )
    def test_headquarter_type_filter(self, setup_headquarters_data, query, results):
        """Test headquarter type filter."""
        url = reverse('api-v4:search:company')
        response = self.api_client.post(
            url,
            query,
        )

        assert response.status_code == status.HTTP_200_OK

        num_results = len(results)
        assert response.data['count'] == num_results
        assert len(response.data['results']) == num_results

        search_results = {company['name'] for company in response.data['results']}
        assert search_results == results

    def test_global_headquarters(self, setup_es):
        """Test global headquarters filter."""
        ghq1 = CompanyFactory(headquarter_type_id=constants.HeadquarterType.ghq.value.id)
        ghq2 = CompanyFactory(headquarter_type_id=constants.HeadquarterType.ghq.value.id)
        companies = CompanyFactory.create_batch(5, global_headquarters=ghq1)
        CompanyFactory.create_batch(5, global_headquarters=ghq2)
        CompanyFactory.create_batch(10)

        setup_es.indices.refresh()

        url = reverse('api-v4:search:company')
        response = self.api_client.post(
            url,
            {
                'global_headquarters': ghq1.id,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        assert response.data['count'] == 5
        assert len(response.data['results']) == 5

        search_results = {UUID(company['id']) for company in response.data['results']}
        assert search_results == {company.id for company in companies}

    @pytest.mark.parametrize(
        'sector_level',
        (0, 1, 2),
    )
    def test_sector_descends_filter(self, hierarchical_sectors, setup_es, sector_level):
        """Test the sector_descends filter."""
        num_sectors = len(hierarchical_sectors)
        sectors_ids = [sector.pk for sector in hierarchical_sectors]

        companies = CompanyFactory.create_batch(
            num_sectors,
            sector_id=factory.Iterator(sectors_ids),
        )
        CompanyFactory.create_batch(
            3,
            sector=factory.LazyFunction(lambda: random_obj_for_queryset(
                Sector.objects.exclude(pk__in=sectors_ids),
            )),
        )

        setup_es.indices.refresh()

        url = reverse('api-v4:search:company')
        body = {
            'sector_descends': hierarchical_sectors[sector_level].pk,
        }
        response = self.api_client.post(url, body)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == num_sectors - sector_level

        actual_ids = {UUID(company['id']) for company in response_data['results']}
        expected_ids = {company.pk for company in companies[sector_level:]}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize(
        'country,match',
        (
            (constants.Country.cayman_islands.value.id, True),
            (constants.Country.montserrat.value.id, True),
            (constants.Country.azerbaijan.value.id, False),
            (constants.Country.anguilla.value.id, False),
        ),
    )
    def test_composite_country_filter(self, setup_es, country, match):
        """Tests composite country filter."""
        company = CompanyFactory(
            trading_address_country_id=constants.Country.cayman_islands.value.id,
            registered_address_country_id=constants.Country.montserrat.value.id,
        )
        setup_es.indices.refresh()

        url = reverse('api-v4:search:company')

        response = self.api_client.post(
            url,
            data={
                'country': country,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        if match:
            assert response.data['count'] == 1
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['id'] == str(company.id)
        else:
            assert response.data['count'] == 0
            assert len(response.data['results']) == 0

    @pytest.mark.parametrize(
        'name_term,matched_company_name',
        (
            # name
            ('whiskers', 'whiskers and tabby'),
            ('whi', 'whiskers and tabby'),
            ('his', 'whiskers and tabby'),
            ('ers', 'whiskers and tabby'),
            ('1a', '1a'),

            # trading names
            ('maine coon egyptian mau', 'whiskers and tabby'),
            ('maine', 'whiskers and tabby'),
            ('mau', 'whiskers and tabby'),
            ('ine oon', 'whiskers and tabby'),
            ('ine mau', 'whiskers and tabby'),
            ('3a', '1a'),

            # non-matches
            ('whi lorem', None),
            ('wh', None),
            ('whe', None),
            ('tiger', None),
            ('panda', None),
            ('moine', None),
        ),
    )
    def test_composite_name_filter(self, setup_es, name_term, matched_company_name):
        """Tests composite name filter."""
        CompanyFactory(
            name='whiskers and tabby',
            trading_names=['Maine Coon', 'Egyptian Mau'],
        )
        CompanyFactory(
            name='1a',
            trading_names=['3a', '4a'],
        )
        setup_es.indices.refresh()

        url = reverse('api-v4:search:company')

        response = self.api_client.post(
            url,
            data={
                'name': name_term,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        match = Company.objects.filter(name=matched_company_name).first()
        if match:
            assert response.data['count'] == 1
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['id'] == str(match.id)
        else:
            assert response.data['count'] == 0
            assert len(response.data['results']) == 0

    def test_company_search_paging(self, setup_es):
        """
        Tests the pagination.

        The sortby is not passed in so records are ordered by id.
        """
        total_records = 9
        page_size = 2

        ids = sorted((uuid4() for _ in range(total_records)))

        name = 'test record'

        CompanyFactory.create_batch(
            len(ids),
            id=factory.Iterator(ids),
            name=name,
            trading_names=[],
        )

        setup_es.indices.refresh()

        url = reverse('api-v4:search:company')
        for page in range((len(ids) + page_size - 1) // page_size):
            response = self.api_client.post(
                url,
                data={
                    'original_query': name,
                    'offset': page * page_size,
                    'limit': page_size,
                },
            )

            assert response.status_code == status.HTTP_200_OK

            start = page * page_size
            end = start + page_size
            assert [
                UUID(company['id']) for company in response.data['results']
            ] == ids[start:end]


class TestCompanyExportView(APITestMixin):
    """Tests the company export view."""

    @pytest.mark.parametrize(
        'permissions',
        (
            (),
            (CompanyPermission.view_company,),
            (CompanyPermission.export_company,),
        ),
    )
    def test_user_without_permission_cannot_export(self, setup_es, permissions):
        """Test that a user without the correct permissions cannot export data."""
        user = create_test_user(dit_team=TeamFactory(), permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:search:company-export')
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'request_sortby,orm_ordering',
        (
            ('name', 'name'),
            ('modified_on', 'modified_on'),
            ('modified_on:desc', '-modified_on'),
        ),
    )
    def test_export(
        self,
        setup_es,
        request_sortby,
        orm_ordering,
    ):
        """Test export of company search results."""
        CompanyFactory.create_batch(
            3,
            turnover=None,
            is_turnover_estimated=None,
            number_of_employees=None,
            is_number_of_employees_estimated=None,
        )
        CompanyFactory.create_batch(
            2,
            hq=True,
            turnover=100,
            is_turnover_estimated=True,
            number_of_employees=95,
            is_number_of_employees_estimated=True,
        )

        setup_es.indices.refresh()

        data = {}
        if request_sortby:
            data['sortby'] = request_sortby

        url = reverse('api-v4:search:company-export')

        with freeze_time('2018-01-01 11:12:13'):
            response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert parse_header(response.get('Content-Type')) == ('text/csv', {'charset': 'utf-8'})
        assert parse_header(response.get('Content-Disposition')) == (
            'attachment', {'filename': 'Data Hub - Companies - 2018-01-01-11-12-13.csv'},
        )

        sorted_company = Company.objects.order_by(orm_ordering, 'pk')
        reader = DictReader(StringIO(response.getvalue().decode('utf-8-sig')))

        assert reader.fieldnames == list(SearchCompanyExportAPIView.field_titles.values())

        expected_row_data = [
            {
                'Name': company.name,
                'Link': f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["company"]}/{company.pk}',
                'Sector': get_attr_or_none(company, 'sector.name'),
                'Country': get_attr_or_none(company, 'address_country.name'),
                'UK region': get_attr_or_none(company, 'uk_region.name'),
                'Archived': company.archived,
                'Date created': company.created_on,
                'Number of employees': (
                    company.number_of_employees
                    if company.number_of_employees is not None
                    else get_attr_or_none(company, 'employee_range.name')
                ),
                'Annual turnover': (
                    f'${company.turnover}'
                    if company.turnover is not None
                    else get_attr_or_none(company, 'turnover_range.name')
                ),
                'Headquarter type':
                    (get_attr_or_none(company, 'headquarter_type.name') or '').upper(),
            }
            for company in sorted_company
        ]

        assert list(dict(row) for row in reader) == format_csv_data(expected_row_data)


class TestAutocompleteSearch(APITestMixin):
    """Tests for autocomplete search views."""

    def test_no_permissions_returns_403(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:search:company-autocomplete-search')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_response_body(self, setup_es):
        """Tests the response body of autocomplete search query."""
        company = CompanyFactory(
            name='abc',
            trading_names=['Xyz trading', 'Abc trading'],
        )
        setup_es.indices.refresh()

        url = reverse('api-v4:search:company-autocomplete-search')
        response = self.api_client.get(url, data={'term': 'abc'})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'count': 1,
            'results': [
                {
                    'id': str(company.id),
                    'name': company.name,
                    'address': {
                        'line_1': company.address_1,
                        'line_2': company.address_2 or '',
                        'town': company.address_town,
                        'county': company.address_county or '',
                        'postcode': company.address_postcode or '',
                        'country': {
                            'id': str(company.trading_address_country.id),
                            'name': company.trading_address_country.name,
                        },
                    },
                    'registered_address': {
                        'line_1': company.registered_address_1,
                        'line_2': company.registered_address_2 or '',
                        'town': company.registered_address_town,
                        'county': company.registered_address_county or '',
                        'postcode': company.registered_address_postcode or '',
                        'country': {
                            'id': str(company.registered_address_country.id),
                            'name': company.registered_address_country.name,
                        },
                    },
                    'trading_names': ['Xyz trading', 'Abc trading'],
                },
            ],
        }

    @pytest.mark.parametrize(
        'data,expected_error',
        (
            (
                {},
                {'term': ['This field is required.']},
            ),
            (
                {'term': 'a', 'limit': 0},
                {'limit': ['Ensure this value is greater than or equal to 1.']},
            ),
            (
                {'term': 'a', 'limit': 'asdf'},
                {'limit': ['A valid integer is required.']},
            ),
        ),
    )
    def test_validation_error(self, data, expected_error, setup_data):
        """Tests case where there is not query provided."""
        url = reverse('api-v4:search:company-autocomplete-search')

        response = self.api_client.get(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    @pytest.mark.parametrize(
        'query,expected_companies',
        (
            ('abc', ['abc defg ltd', 'abc defg us ltd']),
            ('abv', []),
            ('ABC', ['abc defg ltd', 'abc defg us ltd']),
            ('hello', []),
            ('', []),
            (1, []),
            ('abc defg ltd', ['abc defg ltd']),
            ('defg', ['abc defg ltd', 'abc defg us ltd']),
            ('us', ['abc defg us ltd']),
            ('hel', ['abc defg ltd', 'abc defg us ltd']),
            ('qrs', ['abc defg us ltd']),
            ('help qrs', []),
        ),
    )
    def test_searching_with_a_query(self, setup_data, query, expected_companies):
        """Tests case where search queries are provided."""
        url = reverse('api-v4:search:company-autocomplete-search')

        response = self.api_client.get(url, data={'term': query})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == len(expected_companies)

        if expected_companies:
            companies = [result['name'] for result in response.data['results']]
            assert companies == expected_companies

    @pytest.mark.parametrize(
        'limit,expected_companies',
        (
            (10, ['abc defg ltd', 'abc defg us ltd']),  # only 2 found
            (2, ['abc defg ltd', 'abc defg us ltd']),
            (1, ['abc defg ltd']),
        ),
    )
    def test_searching_with_limit(self, setup_data, limit, expected_companies):
        """Tests case where search limit is provided."""
        url = reverse('api-v4:search:company-autocomplete-search')

        response = self.api_client.get(
            url,
            data={
                'term': 'abc',
                'limit': limit,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == len(expected_companies)

        if expected_companies:
            companies = [result['name'] for result in response.data['results']]
            assert companies == expected_companies

    @mock.patch(
        'datahub.search.company.views.'
        'CompanyAutocompleteSearchListAPIViewV4._get_permission_filters',
    )
    def test_raise_datahub_error_when_search_app_has_permission_search_filters(
        self, mock_get_app_permission_filters,
    ):
        """
        Tests if a search app has permission filters, if so autocomplete is not
        permitted and a datahub exception error is raised.
        """
        mock_get_app_permission_filters.return_value = True
        url = reverse('api-v4:search:company-autocomplete-search')
        with pytest.raises(DataHubException) as expected_error:
            self.api_client.get(url, data={'term': 'query'})
        assert (
            str(expected_error.value)
            == 'Unable to apply filtering for autocomplete search request'
        )
