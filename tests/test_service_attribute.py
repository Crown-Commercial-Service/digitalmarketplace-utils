import unittest
from dmutils.service_attribute import (
    Attribute, lowercase_first_character_unless_part_of_acronym
)


class TestAttribute(unittest.TestCase):

    def test_get_data_value_retrieves_correct_value(self):
        self.assertEqual(
            Attribute('24/7, 365 days a year', 'text').value,
            '24/7, 365 days a year'
        )

    def test_get_data_type_handles_empty_data(self):
        self.assertEqual(
            Attribute('', 'text').type,
            'text'
        )
        self.assertEqual(
            Attribute('', 'text').value,
            ''
        )
        self.assertEqual(
            Attribute(None, 'percentage').type,
            'text'
        )
        self.assertEqual(
            Attribute(None, 'percentage').value,
            ''
        )
        self.assertEqual(
            Attribute([], 'list').type,
            'text'
        )
        self.assertEqual(
            Attribute([], 'text').value,
            ''
        )

    def test_an_attribute_with_assurance(self):
        attribute = Attribute(
            {
                'value': 'Managed email service',
                'assurance': 'CESG-assured components'
            },
            'text'
        )
        self.assertEqual(
            attribute.value,
            'Managed email service'
        )
        self.assertEqual(
            attribute.assurance,
            'CESG-assured components'
        )

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
        self.assertEqual(
            attribute.value,
            ['Gold certification', 'Silver certification']
        )
        self.assertEqual(
            attribute.assurance,
            "CESG-assured componenents"
        )

    def test_an_attribute_with_assurance_being_service_provider_assertion(self):
        attribute = Attribute(
            {
                'value': 'Managed email service',
                'assurance': 'Service provider assertion'
            },
            'text'
        )
        self.assertEqual(
            attribute.value,
            'Managed email service'
        )
        self.assertEqual(
            attribute.assurance,
            False
        )

    def test_a_required_attribute_with_no_value(self):
        attribute = Attribute(
            '',
            'text',
            optional=False
        )
        self.assertEqual(attribute.answer_required, True)

    def test_a_required_attribute_with_a_value(self):
        attribute = Attribute(
            'Managed email service',
            'text',
            optional=False
        )
        self.assertEqual(attribute.answer_required, False)

    def test_a_optional_attribute_with_no_value(self):
        attribute = Attribute(
            '',
            'text',
            optional=True
        )
        self.assertEqual(attribute.answer_required, False)

    def test_a_optional_attribute_with_a_value(self):
        attribute = Attribute(
            'Managed email service',
            'text',
            optional=True
        )
        self.assertEqual(attribute.answer_required, False)


class TestHelpers(unittest.TestCase):
    def test_normal_string_can_be_lowercased(self):
        self.assertEqual(
            lowercase_first_character_unless_part_of_acronym(
                "Independent validation of assertion"
            ),
            "independent validation of assertion"
        )

    def test_string_starting_with_acronym_can_be_lowercased(self):
        self.assertEqual(
            lowercase_first_character_unless_part_of_acronym(
                "CESG-assured components"
            ),
            "CESG-assured components"
        )
