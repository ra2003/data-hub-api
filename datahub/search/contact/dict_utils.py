from .. import dict_utils


def computed_address_field(field):
    """Gets Contact address from Company is address_same_as_company."""
    def get_field(contact):
        if contact.address_same_as_company:
            return getattr(contact.company, f'trading_{field}')

        return getattr(contact, field)

    def get_id_name_field(contact):
        return dict_utils.id_name_dict(get_field(contact))

    if field == 'address_country':
        return get_id_name_field

    return get_field
