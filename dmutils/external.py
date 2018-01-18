from flask import Blueprint

external = Blueprint('external', __name__)

# Buyer frontend


@external.route('/<framework_framework>/opportunities/<brief_id>')
def get_brief_by_id(framework_framework, brief_id):
    raise NotImplementedError()


@external.route('/help')
def help():
    raise NotImplementedError()

# Supplier frontend


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
