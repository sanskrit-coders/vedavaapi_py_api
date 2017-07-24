import flask_restplus

from .oauth import OAuthSignIn
from flask import redirect, url_for, request, flash, Blueprint, session

URL_PREFIX = '/v1'
api_blueprint = Blueprint(
  'oauth', __name__,
  template_folder='templates'
)

api = flask_restplus.Api(app=api_blueprint, version='1.0', title='vedavaapi py users API',
                         description='For detailed intro and to report issues: see <a href="https://github.com/vedavaapi/vedavaapi_py_api">here</a>. '
                                     'For a list of JSON schema-s this API uses (referred to by name in docs) see <a href="v1/schemas"> here</a>. <BR>'
                                     'A list of REST and non-REST API routes avalilable on this server: <a href="../sitemap">sitemap</a>.',
                         default_label=api_blueprint.name,
                         prefix=URL_PREFIX, doc='/docs')


@api.route('/users')
class UserListHandler(flask_restplus.Resource):
  def get(self):
    """Just list the users."""
    return "NOT IMPLEMENTED", 404


@api_blueprint.route('/login/<provider>')
def login(provider):
  oauth = OAuthSignIn.get_provider(provider)
  return oauth.authorize()


@api_blueprint.route('/authorized/<provider>')
def authorized(provider):
  oauth = OAuthSignIn.get_provider(provider)
  response = oauth.authorized_response()
  next_url = request.args.get('next') or url_for('index')
  if response is None:
    flash('We weren\'t able to log you in I\'m afraid.')
    return redirect(next_url)

  session['oauth_token'] = oauth.get_session_data(response)
  session['user'] = oauth.get_user().to_json_map()
  return redirect(next_url)


@api_blueprint.route("/logout")
def logout():
  session.pop('oauth_token', None)
  session.pop('user', None)
  return redirect(url_for('home'))