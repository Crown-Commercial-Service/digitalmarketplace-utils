from jinja2.sandbox import SandboxedEnvironment
from filters import format_links, nbsp, smartjoin
from formats import dateformat, datetimeformat, shortdateformat


CUSTOM_FILTERS = {
    'format_links': format_links,
    'nbsp': nbsp,
    'smartjoin': smartjoin,
    'dateformat': dateformat,
    'datetimeformat': datetimeformat,
    'shortdateformat': shortdateformat
}


class DMSandboxedEnvironment(SandboxedEnvironment):
    """DigitalMarketplace environment with filters."""

    def __init__(self, *args, **kwargs):
        super(DMSandboxedEnvironment, self).__init__(*args, **kwargs)
        self.filters.update(CUSTOM_FILTERS)
