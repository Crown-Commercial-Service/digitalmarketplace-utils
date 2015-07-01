from dmutils.user import user_has_role, User


def test_user_has_role():
    assert user_has_role({'users': {'role': 'admin'}}, 'admin')


def test_user_has_role_returns_false_on_invalid_json():
    assert not user_has_role({'in': 'valid'}, 'admin')


def test_user_has_role_returns_false_on_none():
    assert not user_has_role(None, 'admin')


def test_user_has_role_returns_false_on_non_matching_role():
    assert not user_has_role({'users': {'role': 'admin'}}, 'supplier')


def test_User_from_json():
    user = User.from_json({'users': {
        'id': 123,
        'emailAddress': 'test@example.com',
        'locked': False,
    }})

    assert user.id == 123
    assert user.email_address == 'test@example.com'


def test_User_from_json_with_supplier():
    user = User.from_json({'users': {
        'id': 123,
        'emailAddress': 'test@example.com',
        'locked': False,
        'supplier': {
            'supplierId': 321,
            'name': 'test supplier',
        }
    }})
    assert user.id == 123
    assert user.email_address == 'test@example.com'
    assert user.supplier_id == 321
    assert user.supplier_name == 'test supplier'
