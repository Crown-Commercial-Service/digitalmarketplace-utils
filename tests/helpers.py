from datetime import datetime
from io import BytesIO


class IsDatetime(object):
    def __eq__(self, other):
        return isinstance(other, datetime)


class MockFile(BytesIO):
    def __init__(self, initial=b"", filename="", name=""):
        super().__init__(initial)
        self._name = name
        self._filename = filename

    @property
    def name(self):
        return self._name

    @property
    def filename(self):
        # weird flask property
        return self._filename
