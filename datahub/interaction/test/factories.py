import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.metadata.test.factories import ServiceFactory, TeamFactory


class ServiceOfferFactory(factory.django.DjangoModelFactory):
    """Service Offer factory."""

    service = factory.SubFactory(ServiceFactory)
    dit_team = factory.SubFactory(TeamFactory)

    class Meta:  # noqa: D101
        model = 'interaction.ServiceOffer'


class InteractionFactory(factory.django.DjangoModelFactory):
    """Interaction factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    subject = 'foo'
    date = now()
    notes = 'Bar'
    dit_adviser = factory.SubFactory(AdviserFactory)
    service_id = constants.Service.trade_enquiry.value.id
    dit_team_id = constants.Team.healthcare_uk.value.id
    created_on = now()
    interaction_type_id = constants.InteractionType.face_to_face.value.id

    class Meta:  # noqa: D101
        model = 'interaction.Interaction'


class ServiceDeliveryFactory(factory.django.DjangoModelFactory):
    """Service delivery factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    subject = 'foo'
    date = now()
    notes = 'Bar'
    dit_adviser = factory.SubFactory(AdviserFactory)
    created_on = now()
    status_id = constants.ServiceDeliveryStatus.offered.value.id
    uk_region_id = constants.UKRegion.east_midlands.value.id
    feedback = 'foobar'

    class Meta:  # noqa: D101
        model = 'interaction.ServiceDelivery'
