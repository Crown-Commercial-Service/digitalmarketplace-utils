from datetime import datetime, timedelta

from dmutils.email import token_created_before_password_last_changed
from dmutils.formats import DATETIME_FORMAT


def test_returns_true_if_user_changed_password_after_token():

    now = datetime.now()
    yesterday = datetime.today() - timedelta(days=1)

    user = {
        "users": {
            "passwordChangedAt": now.strftime(DATETIME_FORMAT)
        }
    }

    assert token_created_before_password_last_changed(yesterday, user)


def test_returns_false_if_user_changed_password_after_token():

    now = datetime.now()
    tomorrow = datetime.today() + timedelta(days=1)

    user = {
        "users": {
            "passwordChangedAt": now.strftime(DATETIME_FORMAT)
        }
    }

    assert not token_created_before_password_last_changed(tomorrow, user)
