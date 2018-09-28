from dmutils.service_attribute import (
    Attribute, lowercase_first_character_unless_part_of_acronym
)


class TestAttribute:

    def test_get_data_value_retrieves_correct_value(self):
        assert Attribute('24/7, 365 days a year', 'text').value == '24/7, 365 days a year'

    def test_get_data_type_handles_empty_data(self):
        assert Attribute('', 'text').type == 'text'
        assert Attribute('', 'text').value == ''

        assert Attribute(None, 'number').type == 'text'
        assert Attribute(None, 'number').value == ''

        assert Attribute([], 'list').type == 'text'
        assert Attribute([], 'text').value == ''

    def test_an_attribute_with_assurance(self):
        attribute = Attribute(
            {
                'value': 'Managed email service',
                'assurance': 'CESG-assured components'
            },
            'text'
        )
        assert attribute.value == 'Managed email service'
        assert attribute.assurance == 'CESG-assured components'

    def test_rendering_of_list_with_assurance(self):
        attribute = Attribute(
            {
                "value": [
                    'Gold certification', 'Silver certification'
                ],
                "assurance": "CESG-assured componenents"
            },
            'list'
        )
        assert attribute.value == ['Gold certification', 'Silver certification']
        assert attribute.assurance == "CESG-assured componenents"

    def test_an_attribute_with_assurance_being_service_provider_assertion(self):
        attribute = Attribute(
            {
                'value': 'Managed email service',
                'assurance': 'Service provider assertion'
            },
            'text'
        )
        assert attribute.value == 'Managed email service'
        assert attribute.assurance is False

    def test_a_required_attribute_with_no_value(self):
        attribute = Attribute(
            '',
            'text',
            optional=False
        )
        assert attribute.answer_required

    def test_a_required_attribute_with_a_value(self):
        attribute = Attribute(
            'Managed email service',
            'text',
            optional=False
        )
        assert attribute.answer_required is False

    def test_a_optional_attribute_with_no_value(self):
        attribute = Attribute(
            '',
            'text',
            optional=True
        )
        assert attribute.answer_required is False

    def test_a_optional_attribute_with_a_value(self):
        attribute = Attribute(
            'Managed email service',
            'text',
            optional=True
        )
        assert attribute.answer_required is False


class TestHelpers:
    def test_normal_string_can_be_lowercased(self):
        assert lowercase_first_character_unless_part_of_acronym(
            "Independent validation of assertion"
        ) == "independent validation of assertion"

    def test_string_starting_with_acronym_can_be_lowercased(self):
        assert lowercase_first_character_unless_part_of_acronym(
            "CESG-assured components"
        ) == "CESG-assured components"
