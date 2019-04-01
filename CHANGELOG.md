# Digital marketplace utils changelog

Records breaking changes from major version bumps

## 48.0.0

PR [#504](https://github.com/alphagov/digitalmarketplace-utils/pull/509)

`DMMailChimpClient.subscribe_new_email_to_list` now returns an error payload instead of a boolean.

Example responses:

```
{"status": "success", "status_code": 200, "error_type": None}
{"status": "error", "status_code": 400, "error_type": "invalid_email"}
{"status": "error", "status_code": 400, "error_type": "already_subscribed"}
{"status": "error", "status_code": 400, "error_type": "deleted_user"}
{"status": "error", "status_code": 500, "error_type": "unexpected_error"}
```

## 47.0.0

PR [#504](https://github.com/alphagov/digitalmarketplace-utils/pull/504)

Removal of `dmutils.metrics`. This code is no longer used.

## 46.0.0

PR [#488](https://github.com/alphagov/digitalmarketplace-utils/pull/488)

Removal of `DMMandrillClient`.

## 45.0.0

PR [#474](https://github.com/alphagov/digitalmarketplace-utils/pull/474)

Rename dmutils/repoutils/freeze-requirements.py > dmutils/repoutils/freeze_requirements.py as per [pep8](https://www.python.org/dev/peps/pep-0008/#package-and-module-names)

Old code:

```
python -m dmutils.repoutils.freeze-requirements requirements-app.txt
```

New code:

```
python -m dmutils.repoutils.freeze_requirements requirements-app.tx
```

## 44.0.0

PR [#455](https://github.com/alphagov/digitalmarketplace-utils/pull/455)

Upgrade flask to from 0.12.4 to 1.0.2. This has breaking changes for flask apps and therefore has breaking changes for users relying on init_app.

Apps should upgrade to `Flask==1.0.2` using the changelog here http://flask.pocoo.org/docs/1.0/changelog/#version-1-0-2 taking care to note
the breaking changes in [v1.0](http://flask.pocoo.org/docs/1.0/changelog/#version-1-0)


Updates to DMNotifyClient and addition of `DMMandrillClient`:

`DMNotifyClient.__init__ `parameter logger is now keyword-only

`DMNotifyClient.get_error_message` method has been deleted

`DMNotifyClient.send_email` parameter email_address has been renamed to to_email_address

`DMNotifyClient.send_email` parameter template_id has been renamed to template_name_or_id

`DMNotifyClient.get_reference` parameter email_adress has been renamed to to_email_address

dm_mandrill now contains a single class `DMMandrillClient`

`dm_mandrill.send_email` has been deleted. Its functionality has been moved to `DMMandrillClient.send_email`, however the function signature has changed.

`dm_mandrill.get_sent_emails` has been deleted. Its functionality has been moved to `DMMandrillClient.get_sent_emails`, however the function signature has changed.

## 43.0.0

PR [#447](https://github.com/alphagov/digitalmarketplace-utils/pull/447)

This bump removes any handling of [FeatureFlags](https://pypi.org/project/Flask-FeatureFlags/) (in e.g. app init code)
and removes FeatureFlags as a dependency.

Specifically, `dmutils.flask_init.init_app(...)` no longer accepts a `feature_flags` argument and performs no
initialization of FeatureFlags for the app.

`dmutils.status.enabled_since(...)` has been removed.

`dmutils.status.get_app_status(...)` no longer adds a `flags` key to its json dictionary.

The dependency on Flask has been upgraded to Flask 0.12, so potentially apps are going to have to make changes
in concordance with http://flask.pocoo.org/docs/0.12/changelog/

## 42.0.0

PR [#400](https://github.com/alphagov/digitalmarketplace-utils/pull/400)

This bump introduces new classes for using WTForms with the frontend toolkit in a way that is unambiguous.

The fields in `dmutils.forms.fields` module have been rewritten to use the new `DMFieldMixin`. Fields which use the mixin can be identified by the 'DM' prefix.
This update also includes 'DM' widgets which are able to use our template macros from `digitalmarketplace-frontend-toolkit`. If the appropriate Jinja2 templates
are loaded into the app, calling the class will render the form fully without further code.

Apps which use this version of `dmutils` should aim to use the new classes everywhere where WTForms is used so that our code is consistent across the board.

Old code:
```
# app/main/forms/form.py
from flask_wtf import FlaskForm
from dmutils.forms import StripWhitespaceStringField

class NameForm(FlaskForm):
    full_name = StripWhitespaceStringField()
--
# app/templates/name.html
{%
  with
  name = "full_name",
  question = "What is your name?",
  hint = "Enter your full name.",
  value = form.full_name.data,
  error = errors.get("full_name", {}).get("message", None)
%}
  {% include "toolkit/forms/textbox.html" %}
{% endwith %}
```


New code:
```
# app/main/forms/form.py
from flask_wtf import FlaskForm
from dmutils.forms.dm_fields import DMStripWhitespaceStringField

class NameForm(FlaskForm):
    full_name = DMStripWhitespaceStringField(
      "What is your name?",
      hint="Enter your full name.")
--
# app/templates/name.html
{{ form.full_name }}
```


Alternatively (expanded form):
```
# app/main/forms/form.py
from flask_wtf import FlaskForm
from dmutils.forms.dm_fields import DMStripWhitespaceStringField

class NameForm(FlaskForm):
    full_name = DMStripWhitespaceStringField(
      "What is your name?",
      hint="Enter your full name.")
--
# app/templates/name.html
{%
  with
  name = form.full_name.name,
  question = form.full_name.question,
  hint = form.full_name.hint,
  value = form.full_name.value,
  error = form.full_name.error
%}
  {% include "toolkit/forms/textbox.html" %}
{% endwith %}
```

## 41.0.0

PR [431](https://github.com/alphagov/digitalmarketplace-utils/pull/431)

`forms.EmailValidator` no longer inherits from `wtforms.validators.Regexp` and its constructor now only accepts a
single, keyword, argument `message`.

## 40.0.0

PR [414](https://github.com/alphagov/digitalmarketplace-utils/pull/414)

Updated dependency on Flask-FeatureFlags v1.0 must be added to `requirements-app.txt` as this version is not on PyPI.

## 39.0.0

PR [407](https://github.com/alphagov/digitalmarketplace-utils/pull/407)

Updated api_stubs.framework_agreement_details, removing keys `frameworkEndDate` and `frameworkStartDate`. Any references to these will need to be removed.

## 38.0.0

PR [#397](https://github.com/alphagov/digitalmarketplace-utils/pull/397)

https://trello.com/c/iqFcVKpd/14 is a ticket to retire the name `framework_framework` in place of a more descriptive `framework_family` when referencing the 'family' a given framework relates to (e.g. the framework family of G-Cloud 10 is G-Cloud).

Updating the references across our updates requires some breaking changes in interfaces, specifically in this case, `dmutils.api_stubs.brief` and `dmutils.externals.get_brief_by_id`. Any calls to these methods using keyword parameters will need to update the interface.

Old code:
```python
from dmutils import api_stubs, externals

api_stubs.brief(framework_framework='digital-outcomes-and-specialists')

externals.get_brief_by_id('digital-outcomes-and-specialists', 1234)
```


New code:
```python
from dmutils import api_stubs, externals

api_stubs.brief(framework_family='digital-outcomes-and-specialists')

externals.get_brief_by_id(framework_family='digital-outcomes-and-specialists', brief_id=1234)
```

## 37.1.0 (unintentional)

As of this version, due to #399 the `dmutils.forms` module does **not** expose any of its own dependencies.
Namely any code attempting to use the following names from `dmutils.forms` will fail:

```python
OrderedDict  # from collections
chain        # from itertools
re
StringField  # from wtforms
Regexp       # from wtforms.validators
Length       # from wtforms.validators
```

Users should instead be importing these directly from their origin (indicated above).

## 37.0.0

PR [#398](https://github.com/alphagov/digitalmarketplace-utils/pull/398)

This bump introduces a new method to format errors from Flask-WTForms in a consistent way. While this is not technically a breaking change, we should still make changes when this is pulled in to make sure all errors from WTForms are passed into templates in a consistent way. Where we might have referenced errors in templates either from the form directly on `form.errors`, or passed them in as `form_errors`, we should now pass **all** errors into the templating engine as an `errors` variable.

Old code
```python
errors = {
    key: {'question': form[key].label.text, 'input_name': key, 'message': form[key].errors[0]}
    for key, value in form.errors.items()
}
return render_template('blah', form_errors=errors)
```

New code:
```python
return render_template('blah', errors=get_errors_from_wtform(form))
```

## 36.0.0

PR [#376](https://github.com/alphagov/digitalmarketplace-utils/pull/376)

DMMailChimpClient's `get_email_addresses_from_list` method is now a generator and has a reduced default page size of 100 (down from 1000) in an effort to reduce timeouts with the Mailchimp servers. Any code that uses email addresses from `get_email_addresses_from_list` will need to be updated to take account of the fact it returns a generator object rather than a list - mainly, where the result object is iterated over multiple times, this will fail without refactoring or converting the generator to a list object first (though this should be avoided to reap the most benefit from it being a generator).

Old code:
```python
emails = client.get_email_addresses_from_list('xyz')
```

New code (sub-optimal; consider refactoring instead):
```python
emails = list(client.get_email_addresses_from_list('xyz'))
```


## 35.0.0

PR [#371](https://github.com/alphagov/digitalmarketplace-utils/pull/371)

We are dropping support for Python 2, so any libraries that pull this in will need to make sure they are compatible
with Python 3.

## 34.0.0

PR: [#360](https://github.com/alphagov/digitalmarketplace-utils/pull/360)

Remove backwards compatibility for email importing. It is no longer required.

## 33.0.0

Reverting our usage of an interim alphagov fork of odfpy now that our patch has been merged into master and released.
1
ACTION: update your `requirements-app.txt`, removing the alphagov odfpy
github URI (if present).

## 32.0.0

PR: [#355](https://github.com/alphagov/digitalmarketplace-utils/pull/355)

Drops support for `decode_password_reset_token` to allow tokens generated with `current_app.config["SECRET_KEY"]`
as the key. We now only support reset password tokens generated with `current_app.config["SHARED_EMAIL_KEY"]`.

## 31.0.0

PR: [#343](https://github.com/alphagov/digitalmarketplace-utils/pull/343)

Major version bump because we require users of this library to upgrade
to a version of the odfpy that is not in pypi.

ACTION: update your `requirements-app.txt`, copying the github URI in this
repo's `requirements.txt`.

## 30.0.0

PR: [#341](https://github.com/alphagov/digitalmarketplace-utils/pull/341)

### What changed

We don't need to add the user role to tokens when decoding them since now we're using the "send_user_account_email" function to create tokens and the user role should be passed in to that function.

### Example app changes

Old token creation:
```
token = generate_token(
    {
        "role": "supplier",
        "supplier_id": 1234,
        "supplier_name": "Supplier Name",
        "email_address": "supplier@example.com"
    },
    current_app.config['SHARED_EMAIL_KEY'],
    current_app.config['INVITE_EMAIL_SALT']
)
```
New token creation:
```
send_user_account_email(
    'supplier',
    "murilo@example.com",
    current_app.config['NOTIFY_TEMPLATES']['invite_contributor'],
    extra_token_data={
        'supplier_id': 1234,
        'supplier_name': "Supplier Name"
    },
    personalisation={
        'user': "Name",
        'supplier': "Supplier Name"
    }
)
```

## 29.0.0

PR: [#339](https://github.com/alphagov/digitalmarketplace-utils/pull/339)

### What changed

Log time format has changed, so the library update has to be bundled with the
new base docker image version or AWS logs agent will fail to pick up the correct
log event timestamps.

### Example app changes
Old Dockerfile:
```
FROM digitalmarketplace/base-api:2.0.1
```
New Dockerfile:
```
FROM digitalmarketplace/base-api:2.0.5
```

## 28.0.0

PR:

### What changed

`decode_invitation_token()` will now return a dict with an error message if the token is invalid or expired. If expired, the dict will also contain the user role that the token was generated for. This is useful when creating new users as we can use the role to render useful, role specific templates even if the token is expired.

### Example return dicts
Invalid token:
```
    {
      'error': 'token_invalid'
    }
```

Expired token:
```
  {
    'error': 'token_expired',
    'role': 'supplier'
  }
```

### Example app changes
Old:
```
if token is None:
    return render_template('generic-error-page.html')
```
New:
```
if token.get('error') == 'token_invalid':
    return render_template('invalid-token-error-page.html')
elif token.get('error') == 'token_expired':
    return render_template('create-{}-user-error-page.html'.format(token['role']))
```

## 27.0.0

PR: [#306](https://github.com/alphagov/digitalmarketplace-utils/pull/306)

### What changed

`S3` was ported to use `boto3` and in the process changed muchly.

- The constructor takes a `region` kwarg (expecting an aws region name) instead of an explicit `host` kwarg.
- The "move existing" mechanism is now gone in favour of versioned buckets.
- `S3.bucket` is no longer exposed to applications (because using it breaks any boto api abstraction we might have). Places where it was "needed" should instead have the missing required functionality added to `S3`.
- `S3.bucket_name` is now a property.
- `S3.save()` now returns a "key dict" (the same as e.g. `S3.get_key()`) as opposed to a boto `Key` object. Again, this is to provide us with api abstraction.
- `S3.save()` no longer accepts a `move_prefix` argument
- `S3.list()`'s returned "key dict"s won't include a `last_modified` parameter at all if `load_timestamps=False` (instead of including a potentially misleading value)
- `S3.list()` called with `load_timestamps=False` will also return its results in an arbitrary order (instead of a potentially misleading one)
- The `s3` module *does* still expose a `S3ResponseError`, but it is a relabelled boto3 `ClientError`, in a slightly odd gesture to backwards compatibility with consumers that were using that. `ClientError` is raised by boto3 in broadly similar situations to those where boto2 would raise `S3ResponseError`.

(not that I could find any external code that used it) `get_file_size_up_to_maximum` is now `get_file_size`, which is a far more sensible way of presenting the interface given the calling code is going to have to compare the result against `FILE_SIZE_LIMIT` anyway

### Example app changes
Old:
```
# get_key used to return None if path param was None

key = some_bucket.get_key(path_that_might_be_none)
```
New:
```
# get_key will now raise an error if path param is None

key = some_bucket.get_key(path_that_might_be_none) if path_that_might_be_none else None
```

Old:
```
>>> key = my_s3.save(...)
>>> key.get_metadata("timestamp")
"2012-03-04T05:06:07.000000Z"
```

New:
```
>>> key_dict = my_s3.save(...)
>>> key_dict.get("last_modified")
"2012-03-04T05:06:07.000000Z"
```

Old:
```
my_s3 = S3("some-bucket", host="s3-narnia-west-1.amazonaws.com")
```

New:
```
my_s3 = S3("some-bucket", region="narnia-west-1")
```

Old:
```
>>> some_items = my_s3.list()
>>> some_items[0]["last_modified"]
"2012-03-04T05:06:07.000000Z"
```

New:
either
```
>>> # don't do that
```

or

```
>>> some_items = my_s3.list(load_timestamps=True)
>>> some_items[0]["last_modified"]
"2012-03-04T05:06:07.000000Z"
```

or

```
>>> some_item = from_somewhere()  # of unknown provenance
>>> some_item.get("last_modified")
```


## 26.0.0

PR: [#307](https://github.com/alphagov/digitalmarketplace-utils/pull/307)

### What changed

The harded-coded list `formats.LOTS`, that applied to G6, G7 and G8, has been removed, in
favour of getting the lots from the API. Related functions have also been removed: `get_label_for_lot_param`
can be replaced by `lot['name']`, and `lot_to_lot_case` is no longer used.

### Example app code
```
all_frameworks = data_api_client.find_frameworks().get('frameworks')
framework = framework_helpers.get_latest_live_framework(all_frameworks, 'g-cloud')

for lot in framework['lots']:
    ...
```


## 25.0.0

PR: [#302](https://github.com/alphagov/digitalmarketplace-utils/pull/302)

### What changed

`upload_document` and `upload_service_documents` now require an explicit `upload_type`
argument (eg 'documents' or 'submissions' for document uploads).

`S3.short_bucket_name` property is removed, so there's no need to set the attribute
on the mocks.

###Example app change

Old:
```
upload_service_documents(
    uploader, documents_url, draft,
    request.files, section, public=False
)

```

New:
```
upload_service_documents(
    uploader, 'documents', documents_url, draft,
    request.files, section, public=False
)
```


## 24.0.0

PR: [#291](https://github.com/alphagov/digitalmarketplace-utils/pull/291)

### What changed

Normalised email exception classes with new `email.exceptions.EmailError`

###Example app change

Old:
```
from dmutils.email import MandrillException

 ...

except MandrillException
```

New:
```
from dmutils.email.exceptions import EmailError

 ...

except EmailError
```


## 23.0.0

PR: [#288](https://github.com/alphagov/digitalmarketplace-utils/pull/288)

### What changed

`decode_invitation_token` previously accepted a `role` parameter, which it would switch on to assert keys of the encoded token's data. For example, if you passed in 'supplier' it would assert that the token contains 'email_address', 'supplier_id', and 'supplier_name'. The contents of the data encoded shouldn't be the responsibility of the utils app, and is left to the implementing code to either check or not.

### Example app change

Old:
```python

data = decode_invitation_token(token, role='supplier')
# data is guaranteed to contain fields 'email_address', 'supplier_id', 'supplier_name'
```

New:
```python

data = decode_invitation_token(token)
# decode_invitation_token makes no assertions about the contents of the token
assert 'email_address' in data.keys()

```


## 22.0.0

PR: [#286](https://github.com/alphagov/digitalmarketplace-utils/pull/286)

### What changed

We used to be able to use a `|markdown` filter in our jinja templates which would turn markdown formatted strings into [Markup](http://jinja.pocoo.org/docs/dev/api/#jinja2.Markup) strings as well as permit HTML tags.
This opened us up to vulnerabilities where untrusted input might end up going through one of these filters and expose us to a cross-site scripting (XSS) exploit.

Going forward, markdown formatted text will be allowed in specific fields (documented in the [README for digitalmarketplace-frameworks](https://github.com/alphagov/digitalmarketplace-frameworks/blob/4c0502379910d8248f062b8aaf35fc58ce912370/README.md#template-fields)) and then rendered by TemplateFields, handled by the Content Loader.

### Example app change

Old:
```jinja

<h2>Question name: {{ question.name|markdown }}</h2>

```

New:
```jinja

<!-- question.name is now a `TemplateField` which renders markdown when accessed -->
<h2>Question name: {{ question.name }}</h2>

```


## 21.0.0

PR: [#266](https://github.com/alphagov/digitalmarketplace-utils/pull/266)

### What changed

Logs will be written to a file or stdout/stderr based on the value of `DM_LOG_PATH`, even for environments with `DEBUG = True`.
To write logs to stderr `DM_LOG_PATH` should be set to a falsy value (eg `None` or empty string). Currently, most app configs
set `DM_LOG_PATH` to `/var/log/...` in the shared config. This declaration should be moved to Preview/Staging/Production configs,
with the shared default set to `None`.

### Example app change

Old:
```python

class Config(object):
    DM_LOG_PATH = '/var/log/digitalmarketplace/application.log'

class Live(object):
    pass

```

New:
```python

class Config(object):
    DM_LOG_PATH = None

class Live(object):
    DM_LOG_PATH = '/var/log/digitalmarketplace/application.log'

```


## 20.0.0

PR: [#264](https://github.com/alphagov/digitalmarketplace-utils/pull/264)

### What changed

Removed content_loader.py to a separate package which can be found [here](https://github.com/alphagov/digitalmarketplace-content-loader). The associated tests were
moved too. Any app which imported the content loader form dmutils will need to be updated to import
from it's new location. To import the new package, add `git+https://github.com/alphagov/digitalmarketplace-content-loader.git@1.0.0#egg=digitalmarketplace-content-loader==1.0.0`
to it's `requirements.txt`.

Removed a couple of functions from `formats.py`. `format_price` was only used by content_loader
so it made sense to move it to the new package. `format_service_price` is a dependency of `format_price`
and so was also moved. It is imported by the front end apps however so they will need updating to import
from it's new location before they can use this version of dmutils.

Mocked a dependency on `ContentSection` from `test_documents.py`. As `ContentSection` is part of the
content loader and has been moved to the new package, it made sense to mock the dependency.

### Example app change

Old:
```python
from dmutils.content_loader import ContentSection
```

New:
```python
from dmcontent.content_loader import ContentSection
```

## 19.0.0

PR: [#248](https://github.com/alphagov/digitalmarketplace-utils/pull/248)

### What changed

Removed the `lot` parameter from the `.get_error_messages()` method of a `ContentSection`.  It wasn't
being used for anything, so the logic remains unaffected.  Calling `.get_error_messages()` with
the lot slug will from this point forward throw an error.

### Example app change

Old:
```python
section.get_error_messages(errors, lot['slug'])
```

New:
```python
section.get_error_messages(errors)
```

## 18.0.0

PR: [#247](https://github.com/alphagov/digitalmarketplace-utils/pull/247)

### What changed

The `ContentLoader` now takes the question `id` from the contents of the YAML file if it is there.
It still falls back to the file name if there is no `id` in the file. The reason this is a breaking
change is that the `serviceTypes` id is now expected to be taken from the `id` field.

### Example app change

Upgrade [digitalmarketplace-frameworks](https://github.com/alphagov/digitalmarketplace-frameworks) to
version 0.20.0 or above.

## 17.0.0

PR: [#238](https://github.com/alphagov/digitalmarketplace-utils/pull/238)

### What changed

`documents.get_agreement_document_path` no longer takes `supplier_name` argument since uploaded
file paths are constructed using `supplier_id` and `document_name` only.

`documents.get_countersigned_agreement_document_path` has been removed.

### Example app change

Old:
```python
get_agreement_document_path(framework_slug, supplier_id, legal_supplier_name, document_name)
```

New:
```python
get_agreement_document_path(framework_slug, supplier_id, document_name)
```

Old:
```python
get_countersigned_agreement_document_path(framework_slug, supplier_id)
```

New:
```python
from dmutils.documents import COUNTERSIGNED_AGREEMENT_FILENAME

get_agreement_document_path(framework_slug, supplier_id, COUNTERSIGNED_AGREEMENT_FILENAME)
```

## 16.0.0

PR: [#233](https://github.com/alphagov/digitalmarketplace-utils/pull/233)

### What changed

`apiclient` and `audit` were moved to the new [dmapiclient](https://github.com/alphagov/digitalmarketplace-apiclient) package. Changes required to the apps are described in the [dmapiclient changelog](https://github.com/alphagov/digitalmarketplace-apiclient/blob/master/CHANGELOG.md).

Imports from `dmutils.apiclient` and `dmutils.audit` modules have to be changed to
the new package name (eg `from dmapiclient import ...`).

API client logger names have changed from `dmutils.apiclient.*` to `dmapiclient.*`.

### Example app change

1. Add dmapiclient package to `requirements.txt`:

   ```
   git+https://github.com/alphagov/digitalmarketplace-apiclient.git@1.0.1#egg=digitalmarketplace-apiclient==1.0.1
   ```

2. Replace imports from `apiclient` modules:

   Old
   ```
   from dmutils.apiclient.errors import HTTPError
   from dmutils.apiclient import SearchAPIClient
   from dmutils.audit import AuditTypes
   ```

   New
   ```
   from dmapiclient import HTTPError
   from dmapiclient import SearchAPIClient
   from dmapiclient.audit import AuditTypes
   ```

3. Check that `dmapiclient` logger is configured

## 15.0.0

PR: [#210](https://github.com/alphagov/digitalmarketplace-utils/pull/210)

### What changed

Breaking changes:
* `content_builder` module no longer does special handling of pricing fields. The content
  repository must therefore be upgraded along with this change.

### Example app change

Upgrade digitalmarketplace-frameworks to `0.5.0` in `bower.json`

## 14.0.0

PR: [#211](https://github.com/alphagov/digitalmarketplace-utils/pull/211)

### What changed

Breaking changes:
* `ContentSection.id` used in edit section URLs now uses dashes instead of underscores.

Non-breaking changes:
* `ContentBuilder` class renamed to `ContentManifest`
* `.get_builder` is renamed to `.get_manifest`, but the old name is kept as an alias to give
  frontend apps time to update
* Question fields can be now accessed as attributes of `ContentQuestion`
* `service_attribute` is being replaced by `ContetManifest.summary` and `ContentQuestionSummary`

### Example app change

Test URLs referencing section IDs need to be updated:

Old
```
res = self.client.get('/suppliers/frameworks/g-cloud-7/declaration/g_cloud_7_essentials')
```

New
```
res = self.client.get('/suppliers/frameworks/g-cloud-7/declaration/g-cloud-7-essentials')
```

## 13.0.0

PR: [#203](https://github.com/alphagov/digitalmarketplace-utils/pull/203)

### What changed

The method `get_agreement_document_path` in `documents.py` now has supplier name as an additional parameter.

### Example app change
Old
```
path = get_agreement_document_path(framework_slug, supplier_id, document_name)
```

New
```
path = get_agreement_document_path(framework_slug, supplier_id, supplier_name, document_name)
```

## 12.0.0

PR: [#202](https://github.com/alphagov/digitalmarketplace-utils/pull/202)

### What changed

1. Two new parameters were added to `dmutils.apiclient.DataAPIClient.create_new_draft_service`:
   `data` and `page_questions`
2. Parameter order for `dmutils.apiclient.DataAPIClient.create_new_draft_service` was changed to:
   `create_new_draft_service(self, framework_slug, lot, supplier_id, data, user, page_questions=None)`
3. `dmutils.apiclient.DataAPIClient.get_framework_status` method was removed, use `.get_framework`
   instead

### Example app change

Old
```python
draft_service = data_api_client.create_new_draft_service(
    framework_slug, supplier_id, user, lot
)
```

New
```python
draft_service = data_api_client.create_new_draft_service(
    framework_slug, lot, supplier_id, {},
    user, page_questions=None
)
```

## 11.0.0

PR: [#195](https://github.com/alphagov/digitalmarketplace-utils/pull/195)

### What changed

1. Moved the creation of the `manager` instance into `init_manager`.

### Example app change

#### In application's `application.py`

Old
```python
from flask.ext.script import Manager

manager = Manager(application)
init_manager(manager, 5003, ['./app/content/frameworks'])
```

New
```python
from dmutils.flask_init import init_manager

manager = init_manager(application, 5003, ['./app/content/frameworks'])
```

## 10.0.0

PR: [#182](https://github.com/alphagov/digitalmarketplace-utils/pull/182)

### What changed

1. `dmutils.content_loader.ContentLoader` changed to support loading content from multiple frameworks.

### Example app change

#### At application startup

Old
```python
existing_service_content = ContentLoader(
    'app/content/frameworks/g-cloud-6/manifests/edit_service.yml',
    'app/content/frameworks/g-cloud-6/questions/services/'
)
new_service_content = ContentLoader(
    'app/content/frameworks/g-cloud-7/manifests/edit_submission.yml',
    'app/content/frameworks/g-cloud-7/questions/services/'
)
declaration_content = ContentLoader(
    'app/content/frameworks/g-cloud-7/manifests/declaration.yml',
    'app/content/frameworks/g-cloud-7/questions/declaration/'
)
```

New
```python
content_loader = ContentLoader('app/content')
content_loader.load_manifest('g-cloud-6', 'services', 'edit_service')
content_loader.load_manifest('g-cloud-7', 'services', 'edit_submission')
content_loader.load_manifest('g-cloud-7', 'declaration', 'declaration')
```

#### In the views

Old
```python
content = declaration_content.get_builder()
```

New
```python
content = content_loader.get_builder(framework_slug, 'declaration')
```

## 9.0.0

PR: [#178](https://github.com/alphagov/digitalmarketplace-utils/pull/178)

#### What changed

1. `dmutils.apiclient.DataAPIClient.get_selection_answers` was renamed to `dmutils.apiclient.DataAPIClient.get_supplier_declaration`
2. `dmutils.apiclient.DataAPIClient.answer_selection_questions` was renamed to `dmutils.apiclient.DataAPIClient.set_supplier_declaration`
3. The response format for `get_supplier_declaration` is different from that of `get_selection_answers`:
   `{"selectionAnswers": {"questionAnswers": { ... }}}` was replaced with `{"declaration": { ... }}`

#### Example app change

Old
```python
answers = data_api_client.get_selection_answers(
   current_user.supplier_id, 'g-cloud-7'
)['selectionAnswers']['questionAnswers']
```

New
```python
declaration = data_api_client.get_supplier_declaration(
  current_user.supplier_id, 'g-cloud-7'
)['declaration']
```
