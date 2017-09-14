import logging

import flask
import flask_restplus
import sanskrit_data.schema.common as common_data_containers
from flask import redirect, url_for, request, flash, Blueprint, session
from jsonschema import ValidationError
from sanskrit_data.schema.common import JsonObject
from sanskrit_data.schema.users import User, AuthenticationInfo

from vedavaapi_py_api.users import get_db
from vedavaapi_py_api.users.oauth import OAuthSignIn

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

URL_PREFIX = '/v1'
api_blueprint = Blueprint(
  'auth', __name__,
  template_folder='templates'
)

api = flask_restplus.Api(app=api_blueprint, version='1.0', title='vedavaapi py users API',
                         description='For detailed intro and to report issues: see <a href="https://github.com/vedavaapi/vedavaapi_py_api">here</a>. '
                                     'For a list of JSON schema-s this API uses (referred to by name in docs) see <a href="schemas"> here</a>. <BR>'
                                     'A list of REST and non-REST API routes avalilable on this server: <a href="../sitemap">sitemap</a>.',
                         default_label=api_blueprint.name,
                         prefix=URL_PREFIX, doc='/docs')


def is_user_admin():
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
  @api.doc(responses={
    200: 'Success.',
    401: 'Unauthorized - you need to be an admin or atleast a registered user. Use <a href="../auth/v1/oauth_login/google" target="new">google oauth</a> to login and/ or request access at https://github.com/vedavaapi/vedavaapi_py_api .',
  })
  def get(self):
    """Just list the users.

    If the user is not an admin, just the user-db details for the current user are listed.
    PS: Login with <a href="v1/oauth_login/google" target="new">google oauth in a new tab</a>.
    """
    session_user = JsonObject.make_from_dict(session.get('user', None))
    if not is_user_admin():
      if session_user is None or not hasattr(session_user, "_id"):
        return {"message": "No user found, not authorized!"}, 401
      else:
        return [session_user.to_json_map()], 200
    else:
      user_list = [user for user in get_db().find(find_filter={})]
      logging.debug(user_list)
      return user_list, 200

  post_parser = api.parser()
  post_parser.add_argument('jsonStr', location='json', help="Should fit the User schema.")

  @api.expect(post_parser, validate=False)
  # TODO: The below fails silently. Await response on https://github.com/noirbizarre/flask-restplus/issues/194#issuecomment-284703984 .
  @api.expect(User.schema, validate=True)
  @api.doc(responses={
    200: 'Update success.',
    401: 'Unauthorized - you need to be an admin. Use <a href="../auth/v1/oauth_login/google" target="new">google oauth</a> to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
    417: 'JSON schema validation error.',
    409: 'Object with matching info already exists. Please edit that instead or delete it.',
  })
  def post(self):
    """Add a new user, identified by the authentication_infos array.

    PS: Login with <a href="v1/oauth_login/google" target="new">google oauth in a new tab</a>.
    """
    logging.info(str(request.json))
    if not is_user_admin():
      return {"message": "User is not an admin!"}, 401

    user = common_data_containers.JsonObject.make_from_dict(request.json)
    if not isinstance(user, User):
      return {"message": "Input JSON object does not conform to User.schema: " + User.schema}, 417

    # Check to see if there are other entries in the database with identical authentication info.
    for auth_info in user.authentication_infos:
      matching_user = get_db().get_user(auth_info=auth_info)
      if matching_user is not None:
        logging.warning(str(matching_user))
        return {"message": "Object with matching info already exists. Please edit that instead or delete it.",
                "matching_user": matching_user.to_json_map()
                }, 409

    try:
      user.update_collection(db_interface=get_db())
    except ValidationError as e:
      import traceback
      message = {
        "message": "Some input object does not fit the schema.",
        "exception_dump": (traceback.format_exc())
      }
      return message, 417
    return user.to_json_map(), 200


@api.route('/users/<string:id>')
@api.param('id', 'Hint: Get one from the JSON object returned by another GET call. ')
class UserHandler(flask_restplus.Resource):
  # noinspection PyMethodMayBeStatic
  @api.doc(responses={
    200: 'Success.',
    401: 'Unauthorized - you need to be an admin, or you need to be accessing your own data. Use <a href="../auth/v1/oauth_login/google" target="new">google oauth</a> to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
    404: 'id not found'
  })
  def get(self, id):
    """Just get the user info.

    PS: Login with <a href="v1/oauth_login/google" target="new">google oauth in a new tab</a>.
    :param id: String
    :return: A User object.
    """
    matching_user = get_db().find_by_id(id=id)

    if matching_user is None:
      return {"message": "User not found!"}, 404

    session_user = JsonObject.make_from_dict(session.get('user', None))

    if not is_user_admin() and (session_user is None or session_user._id != matching_user._id):
      return {"message": "User is not an admin!"}, 401

    return matching_user, 200

  post_parser = api.parser()
  post_parser.add_argument('jsonStr', location='json')

  @api.expect(post_parser, validate=False)
  # TODO: The below fails silently. Await response on https://github.com/noirbizarre/flask-restplus/issues/194#issuecomment-284703984 .
  @api.expect(User.schema, validate=True)
  @api.doc(responses={
    200: 'Update success.',
    401: 'Unauthorized - you need to be an admin, or you need to be accessing your own data. Use <a href="../auth/v1/oauth_login/google" target="new">google oauth</a> to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
    404: 'id not found',
    417: 'JSON schema validation error.',
    409: 'A different object with matching info already exists. Please edit that instead or delete it.',
  })
  def post(self):
    """Modify a user.

    PS: Login with <a href="v1/oauth_login/google" target="new">google oauth in a new tab</a>.
    """
    matching_user = get_db().find_by_id(id=id)

    if matching_user is None:
      return {"message": "User not found!"}, 404

    session_user = JsonObject.make_from_dict(session.get('user', None))

    logging.info(str(request.json))
    if not is_user_admin() and (session_user is None or session_user._id != matching_user._id):
      return {"message": "Unauthorized!"}, 401
    user = common_data_containers.JsonObject.make_from_dict(request.json)
    if not isinstance(user, User):
      return {"message": "Input JSON object does not conform to User.schema: " + User.schema}, 417
    for auth_info in user.authentication_infos:
      another_matching_user = get_db().get_user(auth_info=auth_info)
      if another_matching_user is not None and another_matching_user._id != matching_user._id:
        logging.warning(str(another_matching_user))
        return {"message": "Another object with matching info already exists. Please delete it first.",
                "another_matching_user": another_matching_user.to_json_map()
                }, 409
    try:
      user.update_collection(db_interface=get_db())
    except ValidationError as e:
      import traceback
      message = {
        "message": "Some input object does not fit the schema.",
        "exception_dump": (traceback.format_exc())
      }
      return message, 417
    return user.to_json_map(), 200

  delete_parser = api.parser()

  @api.expect(delete_parser, validate=False)
  # TODO: The below fails silently. Await response on https://github.com/noirbizarre/flask-restplus/issues/194#issuecomment-284703984 .
  @api.expect(User.schema, validate=True)
  @api.doc(responses={
    200: 'Update success.',
    401: 'Unauthorized - you need to be an admin, or you need to be accessing your own data. Use <a href="../auth/v1/oauth_login/google" target="new">google oauth</a> to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
    404: 'id not found',
  })
  def delete(self):
    """Delete a user.

    PS: Login with <a href="v1/oauth_login/google" target="new">google oauth in a new tab</a>.
    """
    matching_user = get_db().find_by_id(id=id)

    if matching_user is None:
      return {"message": "User not found!"}, 404

    session_user = JsonObject.make_from_dict(session.get('user', None))

    logging.info(str(request.json))
    if not is_user_admin() and (session_user is None or session_user._id != matching_user._id):
      return {"message": "Unauthorized!"}, 401
    matching_user.delete_in_collection(db_interface=get_db())
    return {}, 200


@api.route('/oauth_login/<string:provider>')
class OauthLogin(flask_restplus.Resource):
  get_parser = api.parser()
  get_parser.add_argument('next_url', type=str, location='args')

  @api.expect(get_parser, validate=True)
  def get(self, provider):
    """ Kick-off the oauth process. Will redirect to the oauth provider website first.

    To try this out, try <a href="v1/oauth_login/google" target="new">google oauth in a new tab</a>"""
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize(next_url=request.args.get('next_url'))


@api.route('/oauth_authorized/<string:provider>')
class OauthAuthorized(flask_restplus.Resource):
  get_parser = api.parser()
  get_parser.add_argument('state', type=str, location='args')

  @api.expect(get_parser, validate=True)
  @api.doc(responses={
    200: 'Login success.',
    401: 'Unauthorized.',
  })
  def get(self, provider):
    """The user's browser is redirected to this address after successfully validating with the oauth provider by calling oauth_login."""
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
        logging.warning(
          "For some strange reason, the browser requested this url for a second time. Could be just the user, but investigate.")
      else:
        response = {"exceptionData": e.data}, 401
        return response

    response_code = 200
    if response is None:
      # flash('Couldn\'t authenticate you with ' + provider)
      response_code = 401
    else:
      session['oauth_token'] = oauth.get_session_data(response)
      session['user'] = oauth.get_user().to_json_map()
      logging.debug(session)
      # flash('Authenticated!')

    # logging.debug(request.args)
    # Example request.args: {'code': '4/BukA679ASNPe5xvrbq_2aJXD_OKxjQ5BpCnAsCqX_Io', 'state': 'http://localhost:63342/vedavaapi/ullekhanam-ui/docs/v0/html/viewbook.html?_id=59adf4eed63f84441023762d'}
    next_url = request.args.get('state')
    if next_url is not None:
      # Not using redirect(next_url) because:
      #   Attempting to redirect to file:///home/vvasuki/ullekhanam-ui/docs/v0/html/viewbook.html?_id=59adf4eed63f84441023762d failed with "unsafe redirect."
      return {"message": 'Continue on to <a href="%(url)s">%(url)s</a>' % {"url": next_url}}, response_code
      # return redirect(next_url)
    else:
      return {"message": "Did not get a next_url, it seems!"}, response_code


@api.route('/password_login')
class PasswordLogin(flask_restplus.Resource):
  post_parser = api.parser()
  post_parser.add_argument('user_id', type=str, location='form')
  post_parser.add_argument('user_secret', type=str, location='form')

  @api.expect(post_parser, validate=True)
  @api.doc(responses={
    200: 'Login success.',
    401: 'Unauthorized.',
  })
  def post(self):
    """ Log in with a password.

    Passwords are convenient for authenticating bots.
    For human debugging - just use Google oauth login as an admin (but ensure that url is localhost, not a bare ip address).
    """
    user_id = request.form.get('user_id')
    user_secret = request.form.get('user_secret')
    user = get_db().get_user(auth_info=AuthenticationInfo.from_details(auth_user_id=user_id,
                                                                       auth_provider="vedavaapi"))
    logging.debug(user)
    if user is None:
      return {"message": "No such user_id"}, 401
    else:
      authentication_matches = list(
        filter(lambda info: info.auth_provider == "vedavaapi" and info.check_password(user_secret),
               user.authentication_infos))
      if not authentication_matches or len(authentication_matches) == 0:
        return {"message": "Bad pw"}, 401
      session['user'] = user.to_json_map()
    # logging.debug(request.args)
    # Example request.args: {'code': '4/BukA679ASNPe5xvrbq_2aJXD_OKxjQ5BpCnAsCqX_Io', 'state': 'http://localhost:63342/vedavaapi/ullekhanam-ui/docs/v0/html/viewbook.html?_id=59adf4eed63f84441023762d'}
    next_url = request.args.get('state')
    if next_url is not None:
      # Not using redirect(next_url) because:
      #   Attempting to redirect to file:///home/vvasuki/ullekhanam-ui/docs/v0/html/viewbook.html?_id=59adf4eed63f84441023762d failed with "unsafe redirect."
      return {"message": 'Continue on to <a href="%(url)s">%(url)s</a>' % {"url": next_url}}, 200
      # return redirect(next_url)
    else:
      return {"message": "Did not get a next_url, it seems!"}, 200


@api_blueprint.route("/logout")
class LogoutHandler(flask_restplus.Resource):
  get_parser = api.parser()
  get_parser.add_argument('next_url', type=str, location='args')

  @api.expect(get_parser, validate=True)
  def get(self, next_url):
    session.pop('oauth_token', None)
    session.pop('user', None)
    next_url = request.args.get('next_url')
    if next_url is not None:
      return {"message": 'Continue on to <a href="%(url)s">%(url)s</a>' % {"url": next_url}}, 200
    else:
      return {"message": "Did not get a next_url, it seems!"}, 200


# noinspection PyMethodMayBeStatic
@api.route('/schemas')
class SchemaListHandler(flask_restplus.Resource):
  def get(self):
    """Just list the schemas."""
    from sanskrit_data.schema import common, users
    logging.debug(common.get_schemas(common))
    schemas = common.get_schemas(common)
    schemas.update(common.get_schemas(users))
    return schemas, 200
