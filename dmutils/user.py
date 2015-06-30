def user_has_role(user, role):
    try:
        return user['users']['role'] == role
    except (KeyError, TypeError):
        return False
