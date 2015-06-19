import os
import datetime
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


def enabled_since(date_string):
    if date_string:
        # Check format like YYYY-MM-DD
        datetime.datetime.strptime(date_string, DATE_FORMAT)
        return date_string

    return False
