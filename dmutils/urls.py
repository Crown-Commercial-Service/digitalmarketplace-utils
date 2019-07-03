from pathlib import PurePath
import re

from werkzeug.routing import BaseConverter, ValidationError


class SafePurePathConverter(BaseConverter):
    """
        Like the default :class:`PathConverter`, but it converts
        the output to a :class:`pathlib.PurePath` and ensures it
        contains no path components consisting only of dots.
    """

    regex = "[^/].*?"
    weight = 200

    _disallowed_path_part_re = re.compile(r"\.+$")

    def to_python(self, value):
        pth = PurePath(value)
        if not pth.parts:
            raise ValidationError("All path parts squashed out")

        for part in pth.parts:
            if self._disallowed_path_part_re.match(part):
                raise ValidationError(f"Disallowed path part {part!r}")

        return pth
