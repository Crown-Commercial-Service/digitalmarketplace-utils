Digital Marketplace utils
=========================

[![Coverage Status](https://coveralls.io/repos/alphagov/digitalmarketplace-utils/badge.svg?branch=multiquestion-questions&service=github)](https://coveralls.io/github/alphagov/digitalmarketplace-utils?branch=multiquestion-questions)

## What's in here?

* Digital Marketplace API clients
* Formatting utilities for Digital Marketplace
* Digital Marketplace logging for Flask using JSON Logging
* Utility functions/libraries for Amazon S3, Mailchimp/Mandrill, Cloudwatch
* Helper code for Flask configuration
* A formed version of Flask Feature Flags

## Using FeatureFlags

Hide not-ready-to-ship features until they're ready.

#### Basic implementation

```python
# config.py

class Config(object):
  FEATURE_FLAGS_THING = enabled_since('2015-10-08')
```
```python
# main/views.py

from .. import flask_featureflags

@main.route('/')
def index():
	return render_template("index.html")

@main.route('/shiny-new-thing')
@flask_featureflags.is_active_feature('THING', redirect_to='/')
def shiny_new_thing():
	return render_template("shiny_new_thing.html")
```
```htmldjango
<!-- templates/index.html -->

<p>Content</p>
{% if 'THING' is active_feature %}
	<a href="{{ url_for('.shiny_new_thing') }}">Check out this cool thing!</a>
{% endif %}

```

#### Documentation

[Documentation for the extension lives here](https://flask-featureflags.readthedocs.org/en/latest/).

#### Deviations from source code

1. Only [Inline Flags](https://flask-featureflags.readthedocs.org/en/latest/) are recognized.
	```python
    # Do this
    FEATURE_FLAGS_THING = True

    # Not this
    FEATURE_FLAGS: {
    	'thing': True
    }
    ```

2. [`get_flags()`](https://github.com/alphagov/digitalmarketplace-utils/blob/master/dmutils/status.py#L15   )

	Returns all of the flags and their values set in our config file (for the current environment), but it doesn't know which ones exist elsewhere in the code.
	If you define a flag in the code that isn't in the config file, it will throw an error **but only once you come across it**.

    Hit up the `/_status` endpoint of each app to see which flags are being used (if any).

3. [`enabled_since('yyyy-mm-dd')`](https://github.com/alphagov/digitalmarketplace-utils/blob/master/dmutils/status.py#L28)

	Super simple way of tracking how long flags have been turned on.
	Flags are considered active if they return any truthy value, so by assigning them a date string (ideally, one corresponding to the current date), we'll know when they were activated.

    Accuracy of dates will depend on cognizant developers and vigilant code reviewers.
