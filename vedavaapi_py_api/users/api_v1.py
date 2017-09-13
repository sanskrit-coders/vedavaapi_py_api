import logging

import flask
import flask_restplus
import sanskrit_data.schema.common as common_data_containers
from flask import redirect, url_for, request, flash, Blueprint, session
from jsonschema import ValidationError
from sanskrit_data.schema.common import JsonObject
from sanskrit_data.schema.users import User

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
    401: 'Unauthorized - you need to be an admin. Use ../auth/oauth_login/google to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
  })
  def get(self):
    """Just list the users."""
    if not is_user_admin():
      return {"message": "User is not an admin!"}, 401
    user_list = [user for user in get_db().find(find_filter={})]
    logging.debug(user_list)
    return user_list, 200

  post_parser = api.parser()
  post_parser.add_argument('jsonStr', location='json')

  @api.expect(post_parser, validate=False)
  # TODO: The below fails silently. Await response on https://github.com/noirbizarre/flask-restplus/issues/194#issuecomment-284703984 .
  @api.expect(User.schema, validate=True)
  @api.doc(responses={
    200: 'Update success.',
    401: 'Unauthorized - you need to be an admin. Use ../auth/oauth_login/google to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
    417: 'JSON schema validation error.',
    409: 'Object with matching info already exists. Please edit that instead or delete it.',
  })
  def post(self):
    """Add or modify a user, identified by the authentication_infos array."""
    logging.info(str(request.json))
    if not is_user_admin():
      return {"message": "User is not an admin!"}, 401

    user = common_data_containers.JsonObject.make_from_dict(request.json)
    if not isinstance(user, User):
      return {"message": "Input JSON object does not conform to User.schema: " + User.schema}, 417
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
    401: 'Unauthorized - you need to be an admin, or you need to be accessing your own data. Use ../auth/oauth_login/google to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
    404: 'id not found'
  })
  def get(self, id):
    """Just get the user info.

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
    401: 'Unauthorized - you need to be an admin, or you need to be accessing your own data. Use ../auth/oauth_login/google to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
    404: 'id not found',
    417: 'JSON schema validation error.',
    409: 'A different object with matching info already exists. Please edit that instead or delete it.',
  })
  def post(self):
    """Add or modify a user, identified by the authentication_infos array."""
    matching_user = get_db().find_by_id(id=id)

    if matching_user is None:
      return {"message": "User not found!"}, 404

    session_user = JsonObject.make_from_dict(session.get('user', None))

    logging.info(str(request.json))
    if not is_user_admin() and (session_user is None or session_user._id != matching_user._id):
      return {"message": "User is not an admin!"}, 401
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
      logging.warning(
        "For some strange reason, the browser requested this url for a second time. Could be just the user, but investigate.")
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
  user = get_db().find_one(find_filter={"authentication_infos.auth_user_id": user_id,
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
