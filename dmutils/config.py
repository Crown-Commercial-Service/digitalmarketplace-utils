import os


def init_app(app):
    for key, value in app.config.items():
        if key in os.environ:
            if isinstance(value, bool):
                app.config[key] = _convert_to_boolean_or_fail(key, os.environ[key])
            elif isinstance(value, int):
                app.config[key] = _convert_to_int_or_fail(key, os.environ[key])
            else:
                app.config[key] = os.environ[key]
    app.config['DM_ENVIRONMENT'] = os.environ.get('DM_ENVIRONMENT',
                                                  'development')

    # From Flask 1.0 onwards, ENV is set to either 'production' (default) or 'development'.
    # If set as 'development' then debug mode will be enabled.
    # If left as 'production' when running a local development server, it gives an unsettling warning message.
    # See http://flask.pocoo.org/docs/1.0/config/#environment-and-debug-features
    if app.config['DM_ENVIRONMENT'] == 'development':
        app.config['ENV'] = 'development'


def _convert_to_boolean_or_fail(key, value):
    result = convert_to_boolean(value)
    if not isinstance(result, bool):
        raise ValueError("{} must be boolean".format(key))
    return result


def convert_to_boolean(value):
    """Turn strings to bools if they look like them

    Truthy things should be True
    >>> for truthy in ['true', 'on', 'yes', '1']:
    ...   assert convert_to_boolean(truthy) == True

    Falsey things should be False
    >>> for falsey in ['false', 'off', 'no', '0']:
    ...   assert convert_to_boolean(falsey) == False

    Other things should be unchanged
    >>> for value in ['falsey', 'other', True, 0]:
    ...   assert convert_to_boolean(value) == value
    """
    if isinstance(value, str):
        if value.lower() in ['t', 'true', 'on', 'yes', '1']:
            return True
        elif value.lower() in ['f', 'false', 'off', 'no', '0']:
            return False

    return value


def _convert_to_int_or_fail(key, value):
    result = convert_to_number(value)
    if not isinstance(result, int):
        raise ValueError("{} must be an integer".format(key))
    return result


def convert_to_number(value):
    """Turns numeric looking things into floats or ints

    Integery things should be integers
    >>> for inty in ['0', '1', '2', '99999']:
    ...   assert isinstance(convert_to_number(inty), int)

    Floaty things should be floats
    >>> for floaty in ['0.99', '1.1', '1000.0000001']:
    ...   assert isinstance(convert_to_number(floaty), float)

    Other things should be unchanged
    >>> for value in [0, 'other', True, 123]:
    ...   assert convert_to_number(value) == value
    """
    try:
        return float(value) if "." in value else int(value)
    except (TypeError, ValueError):
        return value
