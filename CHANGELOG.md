# Digital marketplace utils changelog

Records breaking changes from major version bumps

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
