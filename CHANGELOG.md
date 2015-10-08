# Digital marketplace utils changelog

Records breaking changes from major version bumps

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
