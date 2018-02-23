from flask_login import current_user, login_required
from flask import current_app, flash, Markup


ROLES = {
    'buyer': {
        'loginRequiredMessage': Markup("You must log in with a buyer account to see this page."),
    },
    'supplier': {
        'loginRequiredMessage': Markup("You must log in with a supplier account to see this page."),
    },
}


@login_required
def require_login(role):
    """
    Shared function to limit access to a view by role. Can be used with Application.before_request
    or Blueprint.before_request, for example:
        some_blueprint.before_request(functools.partial(require_login, role='buyer'))
    :param role: string, e.g. admin, buyer, supplier
    :return: an unauthorized response, or None if access is allowed (once logged in)
    """
    if current_user.is_authenticated() and current_user.role != role:
        flash(ROLES[role]['loginRequiredMessage'], 'error')
        return current_app.login_manager.unauthorized()
