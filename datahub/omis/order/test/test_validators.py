from unittest import mock
import pytest

from rest_framework.exceptions import ValidationError

from datahub.omis.core.exceptions import Conflict

from .factories import (
    OrderFactory,
    OrderWithCancelledQuoteFactory,
    OrderWithOpenQuoteFactory,
)

from ..constants import OrderStatus
from ..models import Order
from ..validators import (
    ContactWorksAtCompanyValidator,
    NoOtherActiveQuoteExistsValidator,
    OrderDetailsFilledInValidator,
    OrderInStatusValidator,
    ReadonlyAfterCreationValidator,
)


class TestContactWorksAtCompanyValidator:
    """Tests for ContactWorksAtCompanyValidator."""

    def test_contact_from_company(self):
        """
        Test that if the contact specified in data works
        at the company specified in data, the validation passes.
        """
        serializer = mock.Mock()
        company = serializer.instance.company
        new_contact = mock.Mock(company=company)

        validator = ContactWorksAtCompanyValidator()
        validator.set_context(serializer)

        try:
            validator({
                'contact': new_contact,
                'company': company
            })
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_contact_not_from_company(self):
        """
        Test that if the contact specified in data doesn't works
        at the company specified in data, the validation fails.
        """
        serializer = mock.Mock()
        company = serializer.instance.company
        new_contact = mock.Mock()  # doesn't work at `company`

        validator = ContactWorksAtCompanyValidator()
        validator.set_context(serializer)

        with pytest.raises(ValidationError):
            validator({
                'contact': new_contact,
                'company': company
            })

    def test_with_different_field_names(self):
        """
        Test that the validation passes when using different field names.
        """
        serializer = mock.Mock()
        company = serializer.instance.company
        new_main_contact = mock.Mock(company=company)

        validator = ContactWorksAtCompanyValidator(
            contact_field='main_contact',
            company_field='main_company'
        )
        validator.set_context(serializer)

        try:
            validator({
                'main_contact': new_main_contact,
                'main_company': company
            })
        except Exception:
            pytest.fail('Should not raise a validator error.')


class TestReadonlyAfterCreationValidator:
    """Tests for ReadonlyAfterCreationValidator."""

    def test_can_change_when_creating(self):
        """Test that if we are creating the instance, the validation passes."""
        serializer = mock.Mock(instance=None)

        validator = ReadonlyAfterCreationValidator(
            fields=('field1', 'field2')
        )
        validator.set_context(serializer)

        try:
            validator({
                'field1': 'some value',
                'field2': 'some value',
            })
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_cannot_change_after_creation(self):
        """
        Test that if we are updating the instance and we try to update the fields,
        the validation fails.
        """
        serializer = mock.Mock()  # serializer.instance is != None

        validator = ReadonlyAfterCreationValidator(
            fields=('field1', 'field2')
        )
        validator.set_context(serializer)

        with pytest.raises(ValidationError):
            validator({
                'field1': 'some value',
                'field2': 'some value',
            })

    def test_ok_if_the_values_dont_change_after_creation(self):
        """
        Test that if we are updating the instance and we don't update the fields,
        the validation passes.
        """
        serializer = mock.Mock()
        instance = serializer.instance

        validator = ReadonlyAfterCreationValidator(
            fields=('field1', 'field2')
        )
        validator.set_context(serializer)

        try:
            validator({
                'field1': instance.field1,
                'field2': instance.field2,
            })
        except Exception:
            pytest.fail('Should not raise a validator error.')


@pytest.mark.django_db
class TestOrderDetailsFilledInValidator:
    """Tests for the OrderDetailsFilledInValidator."""

    @pytest.mark.parametrize(
        'field,value',
        (
            ('primary_market', None),
            ('service_types', []),
            ('description', ''),
            ('delivery_date', None),
        )
    )
    def test_incomplete_order(self, field, value):
        """Test that an incomplete order doesn't pass the validation."""
        order = OrderFactory()
        setattr(order, field, value)

        validator = OrderDetailsFilledInValidator()
        validator.set_instance(order)

        with pytest.raises(ValidationError):
            validator()

    @pytest.mark.parametrize(
        'field,value',
        (
            ('primary_market', None),
            ('service_types', []),
            ('description', ''),
            ('delivery_date', None),
        )
    )
    def test_incomplete_data(self, field, value):
        """Test that if the data for an order is incomplete, the validation fails."""
        order = OrderFactory()

        validator = OrderDetailsFilledInValidator()
        validator.set_instance(order)

        with pytest.raises(ValidationError):
            validator({field: value})

    def test_complete_order(self):
        """Test that a complete order passes the validation."""
        order = OrderFactory()

        validator = OrderDetailsFilledInValidator()
        validator.set_instance(order)

        try:
            validator()
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_complete_data(self):
        """Test that if the data for an order is complete, the validation passes."""
        order = OrderFactory()  # used only to set up the related props easily

        validator = OrderDetailsFilledInValidator()
        validator.set_instance(Order())  # new order

        try:
            validator({
                'primary_market': order.primary_market,
                'service_types': list(order.service_types.all()),
                'description': 'lorem ipsum',
                'delivery_date': order.delivery_date,
            })
        except Exception:
            pytest.fail('Should not raise a validator error.')


@pytest.mark.django_db
class TestNoOtherActiveQuoteExistsValidator:
    """Tests for the NoOtherActiveQuoteExistsValidator."""

    def test_with_existing_active_quote(self):
        """Test that if there's already an active quote, the validation fails."""
        order = OrderWithOpenQuoteFactory()

        validator = NoOtherActiveQuoteExistsValidator()
        validator.set_instance(order)

        with pytest.raises(Conflict):
            validator()

    def test_without_any_active_quote(self):
        """Test that if there isn't any active quote, the validation passes."""
        order = OrderFactory()

        validator = NoOtherActiveQuoteExistsValidator()
        validator.set_instance(order)

        try:
            validator()
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_with_cancelled_quote(self):
        """Test that if there is a cancelled quote, the validation passes."""
        order = OrderWithCancelledQuoteFactory()

        validator = NoOtherActiveQuoteExistsValidator()
        validator.set_instance(order)

        try:
            validator()
        except Exception:
            pytest.fail('Should not raise a validator error.')


@pytest.mark.django_db
class TestOrderInStatusValidator:
    """Tests for the OrderInStatusValidator."""

    def test_validation_passes(self):
        """
        Test that the validation passes if order.status is one of the allowed statuses.
        """
        order = OrderFactory(status=OrderStatus.complete)

        validator = OrderInStatusValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.complete,
                OrderStatus.cancelled
            )
        )
        validator.set_instance(order)

        try:
            validator()
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_validation_fails(self):
        """
        Test that the validation fails if order.status is NOT one of the allowed statuses.
        """
        order = OrderFactory(status=OrderStatus.complete)

        validator = OrderInStatusValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.cancelled
            )
        )
        validator.set_instance(order)

        with pytest.raises(Conflict):
            validator()

    def test_set_instance_via_serializer_instance(self):
        """
        Test that seriaizer.set_context gets the order from serializer.instance.
        """
        order = Order()
        serializer = mock.Mock(instance=order, context={})

        validator = OrderInStatusValidator(allowed_statuses=())
        validator.set_context(serializer)
        assert validator.instance == order

    def test_set_instance_via_serializer_context(self):
        """
        Test that seriaizer.set_context gets the order from serializer.context['order'].
        """
        order = Order()
        serializer = mock.Mock(context={'order': order})

        validator = OrderInStatusValidator(allowed_statuses=())
        validator.set_context(serializer)
        assert validator.instance == order

    def test_order_not_required(self):
        """
        Test that if order_required == False and the order passed in is None,
        the validation passes.
        """
        validator = OrderInStatusValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.complete,
                OrderStatus.cancelled
            ),
            order_required=False
        )
        validator.set_instance(None)

        try:
            validator()
        except Exception:
            pytest.fail('Should not raise a validator error.')
