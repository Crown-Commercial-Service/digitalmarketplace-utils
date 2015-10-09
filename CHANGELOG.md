# Digital marketplace utils changelog

Records breaking changes from major version bumps

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
content_loader.load_manifest('g-cloud-6', 'edit_service', 'services')
content_loader.load_manifest('g-cloud-7', 'edit_submission', 'services')
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
