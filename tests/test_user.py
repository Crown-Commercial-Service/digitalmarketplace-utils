import pytest
from dmutils.user import user_has_role, User


@pytest.fixture
def user():
    return User(123, 'test@example.com', 321, 'test supplier', False, True)


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
        'active': True
    }})

    assert user.id == 123
    assert user.email_address == 'test@example.com'
    assert not user.is_locked()
    assert user.is_active()


def test_User_from_json_with_supplier():
    user = User.from_json({'users': {
        'id': 123,
        'emailAddress': 'test@example.com',
        'locked': False,
        'active': True,
        'supplier': {
            'supplierId': 321,
            'name': 'test supplier',
        }
    }})
    assert user.id == 123
    assert user.email_address == 'test@example.com'
    assert user.supplier_id == 321
    assert user.supplier_name == 'test supplier'


def test_user_is_active(user):
    user.active = True
    user.locked = False

    assert user.is_active()


def test_user_is_not_active_if_locked(user):
    user.active = True
    user.locked = True

    assert not user.is_active()


def test_user_is_authenticated(user):
    user.active = True
    user.locked = False

    assert user.is_authenticated()


def test_user_is_not_authenticated_if_not_active(user):
    user.active = False
    user.locked = False

    assert not user.is_authenticated()


def test_user_is_not_authenticated_if_locked(user):
    user.active = True
    user.locked = True

    assert not user.is_authenticated()
