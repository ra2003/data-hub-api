from operator import not_

from django.utils.translation import ugettext_lazy
from rest_framework import serializers

from datahub.company.models import Company, Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import is_blank, is_not_blank
from datahub.core.validators import (
    EqualsRule,
    OperatorRule,
    RulesBasedValidator,
    ValidationRule,
)
from datahub.event.models import Event
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
    PolicyArea,
    PolicyIssueType,
    ServiceDeliveryStatus,
)
from datahub.interaction.permissions import HasAssociatedInvestmentProjectValidator
from datahub.investment.serializers import NestedInvestmentProjectField
from datahub.metadata.models import Service, Team


class InteractionSerializer(serializers.ModelSerializer):
    """V3 interaction serialiser."""

    default_error_messages = {
        'invalid_for_non_service_delivery': ugettext_lazy(
            'This field is only valid for service deliveries.',
        ),
        'invalid_for_service_delivery': ugettext_lazy(
            'This field is not valid for service deliveries.',
        ),
        'invalid_for_non_interaction': ugettext_lazy(
            'This field is only valid for interactions.',
        ),
        'invalid_for_non_interaction_or_service_delivery': ugettext_lazy(
            'This value is only valid for interactions and service deliveries.',
        ),
        'invalid_for_non_event': ugettext_lazy(
            'This field is only valid for event service deliveries.',
        ),
        'invalid_when_no_policy_feedback': ugettext_lazy(
            'This field is only valid when policy feedback has been provided.',
        ),
    }

    company = NestedRelatedField(Company)
    contact = NestedRelatedField(
        Contact,
        extra_fields=(
            'name',
            'first_name',
            'last_name',
            'job_title',
        ),
    )
    dit_adviser = NestedAdviserField()
    created_by = NestedAdviserField(read_only=True)
    dit_team = NestedRelatedField(Team)
    communication_channel = NestedRelatedField(
        CommunicationChannel, required=False, allow_null=True,
    )
    is_event = serializers.BooleanField(required=False, allow_null=True)
    event = NestedRelatedField(Event, required=False, allow_null=True)
    investment_project = NestedInvestmentProjectField(required=False, allow_null=True)
    modified_by = NestedAdviserField(read_only=True)
    service = NestedRelatedField(Service)
    service_delivery_status = NestedRelatedField(
        ServiceDeliveryStatus, required=False, allow_null=True,
    )
    policy_areas = NestedRelatedField(PolicyArea, many=True, required=False, allow_empty=True)
    policy_issue_types = NestedRelatedField(
        PolicyIssueType,
        allow_empty=True,
        many=True,
        required=False,
    )

    def validate(self, data):
        """
        Removes the semi-virtual field is_event from the data.

        This is removed because the value is not stored; it is instead inferred from contents
        of the the event field during serialisation.
        """
        if 'is_event' in data:
            del data['is_event']

        if 'contact' in data:
            # Note: null contacts are not allowed in the API
            data['contacts'] = [data['contact']]

        return data

    class Meta:
        model = Interaction
        extra_kwargs = {
            # Date is a datetime in the model, but only the date component is used
            # (at present). Setting the formats as below effectively makes the field
            # behave like a date field without changing the schema and breaking the
            # v1 API.
            'date': {'format': '%Y-%m-%d', 'input_formats': ['%Y-%m-%d']},
            'grant_amount_offered': {'min_value': 0},
            'net_company_receipt': {'min_value': 0},
        }
        fields = (
            'id',
            'company',
            'contact',
            'created_on',
            'created_by',
            'event',
            'is_event',
            'kind',
            'modified_by',
            'modified_on',
            'date',
            'dit_adviser',
            'dit_team',
            'communication_channel',
            'grant_amount_offered',
            'investment_project',
            'net_company_receipt',
            'service',
            'service_delivery_status',
            'subject',
            'notes',
            'archived_documents_url_path',
            'policy_areas',
            'policy_feedback_notes',
            'policy_issue_types',
            'was_policy_feedback_provided',
        )
        read_only_fields = (
            'archived_documents_url_path',
        )
        validators = [
            HasAssociatedInvestmentProjectValidator(),
            RulesBasedValidator(
                ValidationRule(
                    'required',
                    OperatorRule('communication_channel', bool),
                    when=EqualsRule('kind', Interaction.KINDS.interaction),
                ),
                ValidationRule(
                    'invalid_for_non_interaction',
                    OperatorRule('investment_project', not_),
                    when=EqualsRule('kind', Interaction.KINDS.service_delivery),
                ),
                ValidationRule(
                    'invalid_for_service_delivery',
                    OperatorRule('communication_channel', not_),
                    when=EqualsRule('kind', Interaction.KINDS.service_delivery),
                ),
                ValidationRule(
                    'invalid_for_non_service_delivery',
                    OperatorRule('is_event', is_blank),
                    OperatorRule('event', is_blank),
                    OperatorRule('service_delivery_status', is_blank),
                    OperatorRule('grant_amount_offered', is_blank),
                    OperatorRule('net_company_receipt', is_blank),
                    when=EqualsRule('kind', Interaction.KINDS.interaction),
                ),
                ValidationRule(
                    'invalid_when_no_policy_feedback',
                    OperatorRule('policy_issue_types', not_),
                    OperatorRule('policy_areas', not_),
                    OperatorRule('policy_feedback_notes', not_),
                    when=OperatorRule('was_policy_feedback_provided', not_),
                ),
                ValidationRule(
                    'required',
                    OperatorRule('policy_areas', bool),
                    OperatorRule('policy_issue_types', bool),
                    OperatorRule('policy_feedback_notes', is_not_blank),
                    when=OperatorRule('was_policy_feedback_provided', bool),
                ),
                ValidationRule(
                    'required',
                    OperatorRule('is_event', is_not_blank),
                    when=EqualsRule('kind', Interaction.KINDS.service_delivery),
                ),
                ValidationRule(
                    'required',
                    OperatorRule('event', bool),
                    when=OperatorRule('is_event', bool),
                ),
                ValidationRule(
                    'invalid_for_non_event',
                    OperatorRule('event', not_),
                    when=OperatorRule('is_event', not_),
                ),
            ),
        ]
