from datetime import datetime


class IsDatetime(object):
    def __eq__(self, other):
        return isinstance(other, datetime)
