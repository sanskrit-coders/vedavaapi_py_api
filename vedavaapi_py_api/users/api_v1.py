import logging

import flask_restplus
import sanskrit_data.schema.common as common_data_containers
from flask import redirect, url_for, request, flash, Blueprint, session
from sanskrit_data.schema.common import JsonObject
from sanskrit_data.schema.users import User

from vedavaapi_py_api.users.oauth import OAuthSignIn

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


def is_user_admin():
  from flask import session
  user = JsonObject.make_from_dict(session.get('user', None))
  logging.debug(session.get('user', None))
  logging.debug(user)
  if user is None or not user.check_permission(service="users", action="admin"):
    return False
  else:
    return True


@api.route('/users')
class UserListHandler(flask_restplus.Resource):
  # noinspection PyMethodMayBeStatic
  def get(self):
    """Just list the users."""
    return {"message": "NOT IMPLEMENTED"}, 404

  post_parser = api.parser()
  post_parser.add_argument('jsonStr', location='json')

  @api.expect(post_parser, validate=False)
  # TODO: The below fails silently. Await response on https://github.com/noirbizarre/flask-restplus/issues/194#issuecomment-284703984 .
  @api.expect(User.schema, validate=True)
  @api.doc(responses={
    200: 'Update success.',
    401: 'Unauthorized - you need to be an admin. Use ../auth/oauth_login/google to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
    417: 'JSON schema validation error.',
  })
  def post(self):
    """Add or modify a user, identified by the authentication_infos array."""
    logging.info(str(request.json))
    if not is_user_admin():
      return "", 401
    user = common_data_containers.JsonObject.make_from_dict(request.json)
    if not isinstance(user, User):
      return "", 417
    logging.debug(str(User.schema))
    pass


@api_blueprint.route('/oauth_login/<provider>')
def oauth_login(provider):
  oauth = OAuthSignIn.get_provider(provider)
  return oauth.authorize(next_url=request.args.get('next_url'))


@api_blueprint.route('/oauth_authorized/<provider>')
def oauth_authorized(provider):
  oauth = OAuthSignIn.get_provider(provider)
  response = oauth.authorized_response()
  # Example response: {
  #   'expires_in': 3600,
  #   'id_token': 'AsxTQ6wA3xM006J1pGyWd4lmcwowV9nNI1w6SNeP1Qxu1YJ69_w',
  #   'token_type': 'Bearer',
  #   'access_token': '-DlJU'}

  # logging.debug(request.args)
  # Example request.args: {'code': '4/BukA679ASNPe5xvrbq_2aJXD_OKxjQ5BpCnAsCqX_Io', 'state': 'http://localhost:63342/vedavaapi/ullekhanam-ui/docs/v0/html/viewbook.html?_id=59adf4eed63f84441023762d'}
  next_url = request.args.get('state')

  if response is None:
    flash('We weren\'t able to log you in I\'m afraid.')
  else:
    session['oauth_token'] = oauth.get_session_data(response)
    session['user'] = oauth.get_user().to_json_map()
    flash('Authenticated!')
  if next_url is not None:
    return redirect(next_url)
  else:
    return "Did not get a next_url, it seems!"


# Passwords are convenient for authenticating bots.
# For human debugging - just use Google oauth login as an admin (but ensure that url is localhost, not a bare ip address).
@api_blueprint.route('/password_login')
def password_login():
  client_id = request.form.get('client_id')
  client_secret = request.form.get('client_secret')
  from vedavaapi_py_api.users import users_db
  user = users_db.find_one(find_filter={"authentication_infos.auth_user_id": client_id,
                                        "authentication_infos.auth_provider": "vedavaapi",
                                        })
  logging.debug(user)
  if user is None:
    return {"message": "No such client_id"}, 403
  else:
    authentication_matches = list(
      filter(lambda info: info.auth_provider == "vedavaapi" and info.check_password(client_secret),
             user.authentication_infos))
    if not authentication_matches or len(authentication_matches) == 0:
      return {"message": "Bad pw"}, 403
    session['user'] = user
    return {"message": "Welcome " + client_id}, 302


@api_blueprint.route("/logout")
def logout():
  session.pop('oauth_token', None)
  session.pop('user', None)
  return redirect(url_for('index'))