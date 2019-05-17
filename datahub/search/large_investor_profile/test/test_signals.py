from unittest import mock

import pytest
from elasticsearch.exceptions import NotFoundError

from datahub.company.test.factories import CompanyFactory
from datahub.investment.investor_profile.test.factories import LargeCapitalInvestorProfileFactory
from datahub.search.large_investor_profile.apps import LargeInvestorProfileSearchApp

pytestmark = pytest.mark.django_db


def _get_es_document(setup_es, pk):
    return setup_es.get(
        index=LargeInvestorProfileSearchApp.es_model.get_read_alias(),
        doc_type=LargeInvestorProfileSearchApp.name,
        id=pk,
    )


def test_new_large_investor_profile_synced(setup_es):
    """Test that new large capital profiles are synced to ES."""
    investor_profile = LargeCapitalInvestorProfileFactory()
    setup_es.indices.refresh()
    assert _get_es_document(setup_es, investor_profile.pk)


def test_updated_large_investor_profile_synced(setup_es):
    """Test that when an large investor profile is updated it is synced to ES."""
    large_investor_profile = LargeCapitalInvestorProfileFactory()
    large_investor_profile.investable_capital = 12345
    large_investor_profile.save()
    setup_es.indices.refresh()


@pytest.mark.parametrize(
    'investor_profile_factory,expected_in_index,expected_to_call_delete',
    (
        (LargeCapitalInvestorProfileFactory, True, True),
    ),
)
def test_delete_from_es(
    investor_profile_factory, expected_in_index, expected_to_call_delete, setup_es,
):
    """
    Test that when an large investor profile is deleted from db it is also
    calls delete document to delete from ES.
    """
    investor_profile = investor_profile_factory()
    setup_es.indices.refresh()

    if expected_in_index:
        assert _get_es_document(setup_es, investor_profile.pk)
    else:
        with pytest.raises(NotFoundError):
            assert _get_es_document(setup_es, investor_profile.pk) is None

    with mock.patch(
        'datahub.search.large_investor_profile.signals.delete_document',
    ) as mock_delete_document:
        investor_profile.delete()
        setup_es.indices.refresh()
        assert mock_delete_document.called == expected_in_index


def test_edit_company_syncs_large_investor_profile_in_es(setup_es):
    """Tests that updating company details also updated the relevant investor profiles."""
    new_company_name = 'SYNC TEST'
    investor_company = CompanyFactory()
    investor_profile = LargeCapitalInvestorProfileFactory(investor_company=investor_company)
    setup_es.indices.refresh()
    investor_company.name = new_company_name
    investor_company.save()

    result = _get_es_document(setup_es, investor_profile.pk)
    assert result['_source']['investor_company']['name'] == new_company_name
