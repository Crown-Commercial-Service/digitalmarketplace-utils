class Attribute(object):
    """Wrapper to handle accessing an attribute in service_data"""

    def __init__(
        self,
        value,
        question_type,
        label='',
        optional=False,
    ):
        self.label = label
        self.answer_required = False
        if value in ['', [], None]:
            self.value = ''
            self.type = 'text'
            self.assurance = False
            if not optional:
                self.answer_required = True
        else:
            self.value, self.assurance = self._unpack_assurance(value)
            self.type = question_type

    def _unpack_assurance(self, value):
        if (
            isinstance(value, dict) and
            'assurance' in value
        ):
            if (value['assurance'] == 'Service provider assertion'):
                assurance = False
            else:
                assurance = lowercase_first_character_unless_part_of_acronym(
                    value['assurance']
                )
            return (value['value'], assurance)
        else:
            return (value, False)


def lowercase_first_character_unless_part_of_acronym(string):
    if not string:
        return ''
    if string[1:2] == string[1:2].upper():
        return string
    return string[:1].lower() + string[1:]
