from jinja2.sandbox import SandboxedEnvironment

from .filters import format_links, nbsp, smartjoin, sub_country_codes
from .formats import dateformat, datetimeformat, datetodatetimeformat, shortdateformat


CUSTOM_FILTERS = {
    'format_links': format_links,
    'nbsp': nbsp,
    'smartjoin': smartjoin,
    'dateformat': dateformat,
    'datetimeformat': datetimeformat,
    'shortdateformat': shortdateformat,
    'datetodatetimeformat': datetodatetimeformat,
    'sub_country_codes': sub_country_codes,
}


class DMSandboxedEnvironment(SandboxedEnvironment):
    """DigitalMarketplace environment with filters."""

    def __init__(self, *args, **kwargs):
        super(DMSandboxedEnvironment, self).__init__(*args, **kwargs)
        self.filters.update(CUSTOM_FILTERS)
