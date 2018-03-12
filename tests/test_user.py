import mock
import pytest
from dmutils.user import user_has_role, User


@pytest.fixture
def user():
    return User(123, 'test@example.com', 321, 'test supplier', 'micro', False, True, "Name", 'supplier', True)


def test_user_has_role():
    assert user_has_role({'users': {'role': 'admin'}}, 'admin')


def test_user_has_role_returns_false_on_invalid_json():
    assert not user_has_role({'in': 'valid'}, 'admin')


def test_user_has_role_returns_false_on_none():
    assert not user_has_role(None, 'admin')


def test_user_has_role_returns_false_on_non_matching_role():
    assert not user_has_role({'users': {'role': 'admin'}}, 'supplier')


def test_User_from_json():
    admin_user = User.from_json({'users': {
        'id': 123,
        'emailAddress': 'test@example.com',
        'locked': False,
        'active': True,
        'name': 'Name',
        'role': 'admin',
        "userResearchOptedIn": True
    }})

    assert admin_user.id == 123
    assert admin_user.name == 'Name'
    assert admin_user.role == 'admin'
    assert admin_user.email_address == 'test@example.com'
    assert not admin_user.is_locked()
    assert admin_user.is_active()
    assert admin_user.user_research_opted_in


def test_User_from_json_with_supplier():
    supplier_user = User.from_json({'users': {
        'id': 123,
        'name': 'Name',
        'role': 'supplier',
        'emailAddress': 'test@example.com',
        'locked': False,
        'active': True,
        'supplier': {
            'supplierId': 321,
            'name': 'test supplier',
            'organisationSize': 'micro'
        },
        "userResearchOptedIn": True
    }})
    assert supplier_user.id == 123
    assert supplier_user.name == 'Name'
    assert supplier_user.role == 'supplier'
    assert supplier_user.email_address == 'test@example.com'
    assert supplier_user.supplier_id == 321
    assert supplier_user.supplier_name == 'test supplier'
    assert supplier_user.supplier_organisation_size == 'micro'
    assert supplier_user.user_research_opted_in


def test_User_from_json_with_supplier_no_organisation_size():
    supplier_user = User.from_json({'users': {
        'id': 123,
        'name': 'Name',
        'role': 'supplier',
        'emailAddress': 'test@example.com',
        'locked': False,
        'active': True,
        'supplier': {
            'supplierId': 321,
            'name': 'test supplier'
        },
        "userResearchOptedIn": True
    }})
    assert supplier_user.supplier_organisation_size is None


def test_User_has_role(user_json):
    supplier_user = User.from_json(user_json)
    assert supplier_user.has_role('supplier')
    assert not supplier_user.has_role('admin')


def test_User_has_any_role(user_json):
    supplier_user = User.from_json(user_json)
    assert supplier_user.has_any_role('supplier', 'other')
    assert supplier_user.has_any_role('other', 'supplier')
    assert not supplier_user.has_any_role('other', 'admin')


def test_User_load_user(user_json):
    data_api_client = mock.Mock()
    data_api_client.get_user.return_value = user_json

    loaded_user = User.load_user(data_api_client, 123)

    data_api_client.get_user.assert_called_once_with(user_id=123)
    assert loaded_user is not None
    assert loaded_user.id == 123


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


def test_user_research_opt_in(user_json):
    user = User.from_json(user_json)
    assert user.user_research_opted_in


def test_user_research_not_opt_in():
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
            'organisationSize': 'micro'
        },
        "userResearchOptedIn": False
    }})
    assert not user.user_research_opted_in
