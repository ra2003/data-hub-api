from contextlib import suppress

import pytest
from django.core.exceptions import FieldDoesNotExist
from rest_framework import status
from rest_framework.reverse import reverse

from .. import urls
from ..registry import registry

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def pytest_generate_tests(metafunc):
    """
    Parametrizes the tests that use the `metadata_view_name` fixture
    by getting all the metadata from the different apps.

    Parametrizes the tests that use the `ordered_mapping` fixture
    by getting all the ordered metadata from the different apps.
    """
    if 'metadata_view_name' in metafunc.fixturenames:
        view_names = registry.mappings.keys()
        metafunc.parametrize(
            'metadata_view_name',
            view_names,
            ids=[f'{view_name} metadata view' for view_name in view_names]
        )

    if 'ordered_mapping' in metafunc.fixturenames:
        view_data = []
        for view_id, mapping in registry.mappings.items():
            with suppress(FieldDoesNotExist):
                mapping.model._meta.get_field('order')  # check if model has field order
                view_data.append((view_id, mapping.model))

        metafunc.parametrize(
            'ordered_mapping',
            view_data,
            ids=[f'{view_data_item[0]} ordered metadata view' for view_data_item in view_data]
        )


def test_metadata_view_get(metadata_view_name, api_client):
    """Test a metadata view for 200 only."""
    url = reverse(viewname=metadata_view_name)
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK


def test_metadata_view_post(metadata_view_name, api_client):
    """Test views are read only."""
    url = reverse(viewname=metadata_view_name)
    response = api_client.post(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_metadata_view_put(metadata_view_name, api_client):
    """Test views are read only."""
    url = reverse(viewname=metadata_view_name)
    response = api_client.put(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_metadata_view_patch(metadata_view_name, api_client):
    """Test views are read only."""
    url = reverse(viewname=metadata_view_name)
    response = api_client.patch(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_view_name_generation():
    """Test urls are generated correctly."""
    patterns = urls.urlpatterns
    assert {pattern.name for pattern in patterns} == registry.mappings.keys()


def test_ordered_metadata_order_view(ordered_mapping, api_client):
    """
    Test that views with BaseOrderedConstantModel are ordered by the `order` field.
    """
    metadata_view_name, model = ordered_mapping

    url = reverse(viewname=metadata_view_name)
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_names = [value['name'] for value in response.json()]
    assert response_names == list(model.objects.order_by('order').values_list('name', flat=True))


def test_team_view(api_client):
    """Test that the team view returns role, uk_region and country as well."""
    url = reverse(viewname='team')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0] == {
        'id': 'cff02898-9698-e211-a939-e4115bead28a',
        'name': 'Aberdeen City Council',
        'role': {
            'name': 'ATO',
            'id': '846cb21e-6095-e211-a939-e4115bead28a'
        },
        'uk_region': None,
        'country': {
            'name': 'United Kingdom',
            'id': '80756b9a-5d95-e211-a939-e4115bead28a'
        }
    }
