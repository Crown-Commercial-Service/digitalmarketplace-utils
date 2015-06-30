from dmutils.user import user_has_role


def test_user_has_role():
    assert user_has_role({'users': {'role': 'admin'}}, 'admin')


def test_user_has_role_returns_false_on_invalid_json():
    assert not user_has_role({'in': 'valid'}, 'admin')


def test_user_has_role_returns_false_on_none():
    assert not user_has_role(None, 'admin')


def test_user_has_role_returns_false_on_non_matching_role():
    assert not user_has_role({'users': {'role': 'admin'}}, 'supplier')
