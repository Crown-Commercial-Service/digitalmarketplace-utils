import mock
import pytest
from dmutils.user import user_has_role, User


@pytest.fixture
def user():
    return User(123, 'test@example.com', 321, 'test supplier', False, True, "Name", 'supplier')


@pytest.fixture
def user_json():
    return {
        "users": {
            "id": 123,
            "emailAddress": "test@example.com",
            "name": "name",
            "role": "supplier",
            "locked": False,
            "active": True,
            "supplier": {
                "supplierId": 321,
                "name": "test supplier",
            }
        }
    }


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
        'active': True,
        'name': 'Name',
        'role': 'admin',
    }})

    assert user.id == 123
    assert user.name == 'Name'
    assert user.role == 'admin'
    assert user.email_address == 'test@example.com'
    assert not user.is_locked()
    assert user.is_active()


def test_User_from_json_with_supplier():
    user = User.from_json({'users': {
        'id': 123,
        'name': 'Name',
        'role': 'supplier',
        'emailAddress': 'test@example.com',
        'locked': False,
        'active': True,
        'supplier': {
            'supplierId': 321,
            'name': 'test supplier',
        }
    }})
    assert user.id == 123
    assert user.name == 'Name'
    assert user.role == 'supplier'
    assert user.email_address == 'test@example.com'
    assert user.supplier_id == 321
    assert user.supplier_name == 'test supplier'


def test_User_has_role(user_json):
    user = User.from_json(user_json)
    assert user.has_role('supplier')
    assert not user.has_role('admin')


def test_User_load_user(user_json):
    data_api_client = mock.Mock()
    data_api_client.get_user.return_value = user_json

    user = User.load_user(data_api_client, 123)

    data_api_client.get_user.assert_called_once_with(user_id=123)
    assert user is not None
    assert user.id == 123


def test_User_load_user_raises_ValueError_on_non_integer_user_id():
    with pytest.raises(ValueError):
        data_api_client = mock.Mock()
        data_api_client.get_user.return_value = None

        User.load_user(data_api_client, 'foo')

    assert not data_api_client.get_user.called


def test_User_load_user_returns_None_if_no_user_is_found():
    data_api_client = mock.Mock()
    data_api_client.get_user.return_value = None

    loaded_user = User.load_user(data_api_client, 123)

    assert loaded_user is None


def test_User_load_user_returns_None_if_user_is_not_active(user_json):
    user_json['users']['active'] = False
    data_api_client = mock.Mock()
    data_api_client.get_user.return_value = user_json

    loaded_user = User.load_user(data_api_client, 123)

    assert loaded_user is None


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
