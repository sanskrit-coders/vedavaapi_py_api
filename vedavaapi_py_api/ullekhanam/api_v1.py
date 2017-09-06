import logging

import flask_restplus
import sanskrit_data.schema.common as common_data_containers
from flask import Blueprint, request
from sanskrit_data.schema.common import JsonObject

from vedavaapi_py_api.ullekhanam.backend.db import get_db

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

URL_PREFIX = '/v1'
api_blueprint = Blueprint(name='ullekhanam_api', import_name=__name__)
api = flask_restplus.Api(app=api_blueprint, version='1.0', title='vedavaapi py ullekhanam API',
                         description='For detailed intro and to report issues: see <a href="https://github.com/vedavaapi/vedavaapi_py_api">here</a>. '
                                     'For using some API, you need to log in using <a href="../oauth/login/google">google</a>.'
                                     'For a list of JSON schema-s this API uses (referred to by name in docs) see <a href="v1/schemas"> here</a>. <BR>'
                                     'A list of REST and non-REST API routes avalilable on this server: <a href="../sitemap">sitemap</a>. ',
                         default_label=api_blueprint.name,
                         prefix=URL_PREFIX, doc='/docs')


def check_permission():
  from flask import session
  user = JsonObject.make_from_dict(session.get('user', None))
  logging.debug(session.get('user', None))
  logging.debug(user)
  if user is None or not user.check_permission(service="ullekhanam", action="write"):
    return False
  else:
    return True


@api.route('/books')
class BookList(flask_restplus.Resource):
  get_parser = api.parser()
  get_parser.add_argument('pattern', location='args', type='string', default=None)

  @api.expect(get_parser, validate=True)
  # Marshalling as below does not work.
  # @api.marshal_list_with(json_node_model)
  def get(self):
    """ Get booklist.
    
    :return: a list of JsonObjectNode json-s.
    """
    booklist = [book for book in get_db().list_books()]
    logging.debug(booklist)
    return booklist, 200


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
@api.route('/entities/<string:id>')
@api.param('id', 'Hint: Get one from the JSON object returned by another GET call. ')
class EntityHandler(flask_restplus.Resource):
  get_parser = api.parser()
  get_parser.add_argument('depth', location='args', type=int, default=1,
                          help="Do you want children or grandchildren or great grandchildren etc.. of this entity?")

  @api.doc(responses={404: 'id not found'})
  @api.expect(get_parser, validate=True)
  def get(self, id):
    """ Get any entity.
    
    :param id: String

    :return: Entity with descendents in a json tree like:

      {"content": EntityObj, "children": [JsonObjectNode with Child_1, JsonObjectNode with Child_2]}    
    """
    args = self.get_parser.parse_args()
    logging.info("entity get by id = " + id)
    db = get_db()
    entity = common_data_containers.JsonObject.from_id(id=id, db_interface=db)
    if entity is None:
      return "No such entity id", 404
    else:
      node = common_data_containers.JsonObjectNode.from_details(content=entity)
      node.fill_descendents(db_interface=db, depth=args['depth'])
      # pprint(binfo)
      return node.to_json_map(), 200


# noinspection PyUnresolvedReferences
@api.route('/entities/<string:id>/targetters')
class EntityTargettersHandler(flask_restplus.Resource):
  get_parser = api.parser()
  get_parser.add_argument('depth', location='args', type=int, default=10,
                          help="Do you want sub-portions or sub-sub-portions or sub-sub-sub-portions etc..? Minimum 1.")
  get_parser.add_argument('targetter_class', location='args', type=str,
                          help="Example: BookPortion. See jsonClass.enum values in <a href=\"v1/schemas\"> schema</a> definitions.")
  get_parser.add_argument('filter_json', location='args', type=str,
                          help="A brief JSON string with property: value pairs. Currently unimplemented.")

  # noinspection PyShadowingBuiltins
  @api.expect(get_parser, validate=True)
  def get(self, id):
    """ Get all targetters for this entity.
    
    :param id: 

    :return: A list of JsonObjectNode-s with targetters with the following structure.

      {"content": Annotation, "children": [JsonObjectNode with targetting Entity]}    
    """
    logging.info("entity id = " + str(id))
    entity = common_data_containers.JsonObjectWithTarget()
    entity._id = str(id)
    args = self.get_parser.parse_args()
    logging.debug(args["filter_json"])
    targetters = entity.get_targetting_entities(db_interface=get_db(), entity_type=args["targetter_class"])
    targetter_nodes = [
      common_data_containers.JsonObjectNode.from_details(content=annotation)
      for annotation in targetters]
    for node in targetter_nodes:
      node.fill_descendents(db_interface=get_db(), depth=args["depth"] - 1, entity_type=args["targetter_class"])
    return common_data_containers.JsonObject.get_json_map_list(targetter_nodes), 200


@api.route('/entities')
class EntityListHandler(flask_restplus.Resource):
  # input_node = api.model('JsonObjectNode', common_data_containers.JsonObjectNode.schema)

  get_parser = api.parser()
  get_parser.add_argument('filter_json', location='args', type=str,
                          help="A brief JSON string with property: value pairs. Currently unimplemented.")

  @api.expect(get_parser, validate=True)
  def get(self):
    """ Get all matching entities- Currently unimplemented."""
    args = self.get_parser.parse_args()
    logging.debug(args["filter_json"])

  post_parser = api.parser()
  post_parser.add_argument('jsonStr', location='json')

  # TODO: The below fails. Await response on https://github.com/noirbizarre/flask-restplus/issues/194#issuecomment-284703984 .
  # @api.expect(json_node_model, validate=False)

  @api.expect(post_parser, validate=False)
  @api.doc(responses={
    200: 'Update success.',
    401: 'Unauthorized. Use ../oauth/login/google to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
    417: 'JSON schema validation error.',
    418: "Target entity class validation error."
  })
  def post(self):
    """ Add some trees of entities. (You **cannot** add a DAG graph of nodes in one shot - you'll need multiple calls.)
    
    input json:

      A list of JsonObjectNode-s with entities with the following structure.

      {"content": Annotation or BookPortion, "children": [JsonObjectNode with child Annotation or BookPortion]}    

    :return: 

      Same as the input trees, with id-s.
    """
    logging.info(str(request.json))
    if not check_permission():
      return "", 401
    nodes = common_data_containers.JsonObject.make_from_dict_list(request.json)
    for node in nodes:
      from jsonschema import ValidationError
      try:
        node.update_collection(db_interface=get_db())
      except ValidationError as e:
        import traceback
        message = {
          "message": "Some input object does not fit the schema.",
          "exception_dump": (traceback.format_exc())
        }
        return message, 417
      except common_data_containers.TargetValidationError as e:
        import traceback
        message = {
          "message": "Target validation failed.",
          "exception_dump": (traceback.format_exc())
        }
        return message, 418
    return common_data_containers.JsonObject.get_json_map_list(nodes), 200

  @api.expect(post_parser, validate=False)
  @api.doc(responses={
    200: 'Update success.',
    401: 'Unauthorized. Use /oauth/login/google to login and request access at https://github.com/vedavaapi/vedavaapi_py_api .',
  })
  def delete(self):
    """ Delete trees of entities.
    
    input json:

      A list of JsonObjectNode-s with entities with the following structure.

      {"content": Annotation or BookPortion, "children": [JsonObjectNode with child Annotation or BookPortion]}    

    :return: Empty.
    """
    if not check_permission():
      return "", 401
    nodes = common_data_containers.JsonObject.make_from_dict_list(request.json)
    for node in nodes:
      node.delete_in_collection(db_interface=get_db())
    return {}, 200


# noinspection PyMethodMayBeStatic
@api.route('/schemas')
class SchemaListHandler(flask_restplus.Resource):
  def get(self):
    """Just list the schemas."""
    from sanskrit_data.schema import common, books, ullekhanam
    logging.debug(common.get_schemas(common))
    schemas = common.get_schemas(common)
    schemas.update(common.get_schemas(books))
    schemas.update(common.get_schemas(ullekhanam))
    return schemas, 200
