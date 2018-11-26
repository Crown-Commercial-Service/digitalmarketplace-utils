Digital Marketplace utils
=========================

[![Coverage Status](https://coveralls.io/repos/alphagov/digitalmarketplace-utils/badge.svg?branch=master&service=github)](https://coveralls.io/github/alphagov/digitalmarketplace-utils?branch=master)
[![Requirements Status](https://requires.io/github/alphagov/digitalmarketplace-utils/requirements.svg?branch=master)](https://requires.io/github/alphagov/digitalmarketplace-utils/requirements/?branch=master)
![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)

## What's in here?

* Digital Marketplace API clients
* Formatting utilities for Digital Marketplace
* Digital Marketplace logging for Flask using JSON Logging
* Utility functions/libraries for Amazon S3, Mailchimp/Mandrill, Cloudwatch
* Helper code for Flask configuration
* A formed version of Flask Feature Flags

## Logging from applications

When logging from applications you should write your message as a [format
string](https://docs.python.org/2/library/string.html#format-string-syntax) and pass any required
arguments to the log method in the `extra` named argument. This allows our logging to use them as
separate fields in our JSON logs making it much easier to search and aggregate on them.

```python
logger.info("the user {user_id} did the thing '{thing}'", extra={
    'user_id': user_id, 'thing': thing
})
```

Note that apart from not getting the benefit, passing the formatted message can be dangerous. User
generated content may be passed, unescaped to the `.format` method.

## Versioning

Releases of this project follow [semantic versioning](http://semver.org/), ie
> Given a version number MAJOR.MINOR.PATCH, increment the:
>
> - MAJOR version when you make incompatible API changes,
> - MINOR version when you add functionality in a backwards-compatible manner, and
> - PATCH version when you make backwards-compatible bug fixes.

To make a new version:
- update the version in the `dmutils/__init__.py` file
- if you are making a major change, also update the change log;

When the pull request is merged
[a Jenkins job](https://ci.marketplace.team/view/Utils%20and%20toolkit/job/tag-dmutils/)
will be run to tag the new version.
