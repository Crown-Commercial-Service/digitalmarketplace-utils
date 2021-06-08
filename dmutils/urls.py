from pathlib import PurePath
import re

from werkzeug.routing import BaseConverter, ValidationError


def rewrite_supplier_asset_path(url, assets_url):
    """
    Supplier frontend has an authenticated endpoint for declaration documents: frameworks.download_declaration_document

    Sometimes other apps need to be able to show declaration documents to users who are not the supplier who uploaded
    the document. This function allows them to convert the supplier frontend URL into an assets URL.

    You must ensure that you are only exposing this document to authorised users.
    """
    parts = url.split('/suppliers/assets')
    if len(parts) == 2:
        return assets_url + parts[1]
    return url


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
