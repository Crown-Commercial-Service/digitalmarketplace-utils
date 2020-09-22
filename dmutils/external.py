from flask import Blueprint, abort

external = Blueprint('external', __name__)


# Buyer frontend
@external.route('/')
def index():
    raise NotImplementedError()


@external.route('/<framework_family>/opportunities/<brief_id>')
def get_brief_by_id(framework_family, brief_id):
    # The Buyer FE currently hardcodes this route to 'digital-outcomes-and-specialists'
    if framework_family != 'digital-outcomes-and-specialists':
        abort(404)
    raise NotImplementedError()


@external.route('/<framework_family>/opportunities')
def list_opportunities(framework_family):
    # The Buyer FE currently hardcodes this route to 'digital-outcomes-and-specialists'
    if framework_family != 'digital-outcomes-and-specialists':
        abort(404)
    raise NotImplementedError()


@external.route('/<framework_family>/services/<service_id>')
def direct_award_service_page(framework_family, service_id):
    # The Buyer FE currently hardcodes this route to 'g-cloud'
    if framework_family != 'g-cloud':
        abort(404)
    raise NotImplementedError()


@external.route('/g-cloud/suppliers')
def suppliers_list_by_prefix():
    raise NotImplementedError()


@external.route('/help')
def help():
    raise NotImplementedError()


@external.route('/terms-and-conditions')
def terms_and_conditions():
    raise NotImplementedError()


@external.route('/privacy-notice')
def privacy_notice():
    raise NotImplementedError()


@external.route('/accessibility-statement')
def accessibility_statement():
    raise NotImplementedError()


@external.route('/cookies')
def cookies():
    raise NotImplementedError()


# Supplier frontend
@external.route('/suppliers')
def supplier_dashboard():
    raise NotImplementedError()


@external.route('/suppliers/supply')
def become_a_supplier():
    raise NotImplementedError()


# Brief Responses frontend
@external.route('/suppliers/opportunities/<brief_id>/responses/start')
def start_brief_response(brief_id):
    raise NotImplementedError()


@external.route('/suppliers/opportunities/<int:brief_id>/responses/result')
def view_response_result(brief_id):
    raise NotImplementedError()


@external.route('/suppliers/opportunities/frameworks/<framework_slug>')
def opportunities_dashboard(framework_slug):
    raise NotImplementedError()


# Admin frontend
@external.route('/admin')
def admin_dashboard():
    raise NotImplementedError()


# User frontend
@external.route('/user/create/<encoded_token>')
def create_user(encoded_token):
    raise NotImplementedError()


@external.route('/user/login')
def render_login():
    raise NotImplementedError()


@external.route('/user/logout', methods=["POST"])
def user_logout():
    raise NotImplementedError()


@external.route('/user/notifications/user-research')
def user_research_consent():
    raise NotImplementedError()


@external.route('/user/change-password')
def change_password():
    raise NotImplementedError()


@external.route('/user/cookie-settings')
def cookie_settings():
    raise NotImplementedError()


# Briefs frontend
@external.route('/buyers')
def buyer_dashboard():
    raise NotImplementedError()


@external.route('/buyers/create')
def create_buyer_account():
    raise NotImplementedError()


@external.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>')
def info_page_for_starting_a_brief(framework_slug, lot_slug):
    raise NotImplementedError()


@external.route('/buyers/frameworks/<framework_slug>/requirements/user-research-studios')
def studios_start_page(framework_slug):
    raise NotImplementedError()


@external.route('/buyers/frameworks/<framework_slug>/requirements/<lot_slug>/<brief_id>/supplier-questions')
def supplier_questions(framework_slug, lot_slug, brief_id):
    raise NotImplementedError()
