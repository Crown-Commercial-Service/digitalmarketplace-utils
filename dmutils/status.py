import datetime
import math
import os
from .formats import DATE_FORMAT
from flask_featureflags import FEATURE_FLAGS_CONFIG


def get_version_label(path):
    try:
        path = os.path.join(path, 'version_label')
        with open(path) as f:
            return f.read().strip()
    except IOError:
        return None


def get_flags(current_app):
    """ Loop through config variables and return a dictionary of flags.  """
    flags = {}

    for config_var in current_app.config.keys():
        # Check that the (inline) key starts with our config variable
        if config_var.startswith("{}_".format(FEATURE_FLAGS_CONFIG)):

                flags[config_var] = current_app.config[config_var]

    return flags


def get_disk_space_status(low_disk_percent_threshold=5):
    """Accepts a single parameter that indicates the minimum percentage of disk space which should be free for the
    instance to be considered healthy.

    Returns a tuple containing two items: a status (OK or LOW) indicating whether the disk space remaining on the
    instance is below the threshold and the integer percentage remaining disk space."""
    disk_stats = os.statvfs('/')

    disk_free_percent = 100 - int(math.ceil(((disk_stats.f_bfree * 1.0) / disk_stats.f_blocks) * 100))

    return 'OK' if disk_free_percent >= low_disk_percent_threshold else 'LOW', disk_free_percent


def enabled_since(date_string):
    if date_string:
        # Check format like YYYY-MM-DD
        datetime.datetime.strptime(date_string, DATE_FORMAT)
        return date_string

    return False
