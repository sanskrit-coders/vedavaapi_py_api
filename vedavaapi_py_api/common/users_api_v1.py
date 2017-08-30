import logging

import flask_restplus
from flask import redirect, url_for, request, flash, Blueprint, session

from .oauth import OAuthSignIn

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


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
  # noinspection PyMethodMayBeStatic
  def get(self):
    """Just list the users."""
    return {"message": "NOT IMPLEMENTED"}, 404


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


# Passwords are convenient for authenticating bots.
# For human debugging - just use Google oauth login as an admin (but ensure that url is localhost, not a bare ip address).
@api_blueprint.route('/password_login')
def password_login():
  client_id = request.form.get('client_id')
  client_secret = request.form.get('client_secret')
  from vedavaapi_py_api.common.users_db import users_db
  user = users_db.find_one(find_filter={"authentication_infos.auth_user_id": client_id,
                                   "authentication_infos.auth_provider": "vedavaapi",
                                   })
  logging.debug(user)
  if user is None:
    return {"message": "No such client_id"}, 403
  authentication_matches = list(filter(lambda info: info.auth_provider == "vedavaapi" and info.check_password(client_secret), user.authentication_infos))
  if not authentication_matches or len(authentication_matches) == 0:
    return {"message": "Bad pw"}, 403
  session['user'] = user
  return {"message": "Welcome " + client_id}, 302


@api_blueprint.route("/logout")
def logout():
  session.pop('oauth_token', None)
  session.pop('user', None)
  return redirect(url_for('index'))