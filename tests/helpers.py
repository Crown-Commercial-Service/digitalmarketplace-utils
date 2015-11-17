from datetime import datetime
import mock


class IsDatetime(object):
    def __eq__(self, other):
        return isinstance(other, datetime)


def mock_file(filename, length, name=None):
    mock_file = mock.MagicMock()
    mock_file.read.return_value = '*' * length
    mock_file.filename = filename
    mock_file.name = name

    return mock_file
