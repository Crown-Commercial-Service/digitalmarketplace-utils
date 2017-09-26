from datetime import datetime
from six import BytesIO


class IsDatetime(object):
    def __eq__(self, other):
        return isinstance(other, datetime)


class MockFile(BytesIO):
    def __init__(self, initial=b"", filename="", name=""):
        # BytesIO on py2 is an old-style class (yeah, i know...)
        BytesIO.__init__(self, initial)
        self._name = name
        self._filename = filename

    @property
    def name(self):
        return self._name

    @property
    def filename(self):
        # weird flask property
        return self._filename
