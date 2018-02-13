from flask import Blueprint

external = Blueprint('external', __name__)

# Buyer frontend


@external.route('/')
def index():
    raise NotImplementedError()


@external.route('/<framework_framework>/opportunities/<brief_id>')
def get_brief_by_id(framework_framework, brief_id):
    raise NotImplementedError()


@external.route('/g-cloud/suppliers')
def suppliers_list_by_prefix():
    raise NotImplementedError()


@external.route('/help')
def help():
    raise NotImplementedError()


# Supplier frontend

@external.route('/suppliers')
def supplier_dashboard():
    raise NotImplementedError()


@external.route('/suppliers/opportunities/<brief_id>/responses/start')
def start_brief_response(brief_id):
    raise NotImplementedError()


@external.route('/suppliers/opportunities/<int:brief_id>/responses/result')
def view_response_result(brief_id):
    raise NotImplementedError()


@external.route('/suppliers/opportunities/frameworks/<framework_slug>')
def opportunities_dashboard(framework_slug):
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
