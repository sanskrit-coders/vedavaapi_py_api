import logging

import flask
import flask_restplus
import sanskrit_data.schema.common as common_data_containers
import sys
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
  logging.debug(session)
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
      return {"message": "User is not an admin!"}, 401

    user = common_data_containers.JsonObject.make_from_dict(request.json)
    if not isinstance(user, User):
      return {"message": "Input JSON object does not conform to User.schema: " + User.schema}, 417
    logging.debug(str(User.schema))
    pass


@api_blueprint.route('/oauth_login/<provider>')
def oauth_login(provider):
  oauth = OAuthSignIn.get_provider(provider)
  return oauth.authorize(next_url=request.args.get('next_url'))


@api_blueprint.route('/oauth_authorized/<provider>')
def oauth_authorized(provider):
  oauth = OAuthSignIn.get_provider(provider)
  response = None
  from flask_oauthlib.client import OAuthException
  try:
    response = oauth.authorized_response()
    # Example response: {
    #   'expires_in': 3600,
    #   'id_token': 'AsxTQ6wA3xM006J1pGyWd4lmcwowV9nNI1w6SNeP1Qxu1YJ69_w',
    #   'token_type': 'Bearer',
    #   'access_token': '-DlJU'}
  except OAuthException as e:
    import traceback
    logging.warning(traceback.format_exc())
    logging.warning(e.type)
    logging.warning(e.message)
    logging.warning(e.data)
    if (e.data['error_description'] == 'Code was already redeemed.'):
      logging.warning("For some strange reason, the browser requested this url for a second time. Could be just the user, but investigate.")
    else:
      response = flask.json.jsonify(e.data), 401
      return response

  # logging.debug(request.args)
  # Example request.args: {'code': '4/BukA679ASNPe5xvrbq_2aJXD_OKxjQ5BpCnAsCqX_Io', 'state': 'http://localhost:63342/vedavaapi/ullekhanam-ui/docs/v0/html/viewbook.html?_id=59adf4eed63f84441023762d'}
  next_url = request.args.get('state')

  response_code = 200
  if response is None:
    flash('Couldn\'t authenticate you with ' + provider)
    response_code = 401
  else:
    session['oauth_token'] = oauth.get_session_data(response)
    session['user'] = oauth.get_user().to_json_map()
    logging.debug(session)
    flash('Authenticated!')
  if next_url is not None:
    # Not using redirect(next_url) because:
    #   Attempting to redirect to file:///home/vvasuki/ullekhanam-ui/docs/v0/html/viewbook.html?_id=59adf4eed63f84441023762d failed with "unsafe redirect."
    return 'Continue on to <a href="%(url)s">%(url)s</a>' % {"url": next_url}
    # return redirect(next_url)
  else:
    return flask.json.jsonify(message="Did not get a next_url, it seems!"), response_code


# Passwords are convenient for authenticating bots.
# For human debugging - just use Google oauth login as an admin (but ensure that url is localhost, not a bare ip address).
@api_blueprint.route('/password_login')
def password_login():
  user_id = request.form.get('user_id')
  user_secret = request.form.get('user_secret')
  from vedavaapi_py_api.users import users_db
  user = users_db.find_one(find_filter={"authentication_infos.auth_user_id": user_id,
                                        "authentication_infos.auth_provider": "vedavaapi",
                                        })
  logging.debug(user)
  if user is None:
    return {"message": "No such user_id"}, 403
  else:
    authentication_matches = list(
      filter(lambda info: info.auth_provider == "vedavaapi" and info.check_password(user_secret),
             user.authentication_infos))
    if not authentication_matches or len(authentication_matches) == 0:
      return {"message": "Bad pw"}, 403
    session['user'] = user
    return {"message": "Welcome " + user_id}, 302


@api_blueprint.route("/logout")
def logout():
  session.pop('oauth_token', None)
  session.pop('user', None)
  return redirect(url_for('index'))
