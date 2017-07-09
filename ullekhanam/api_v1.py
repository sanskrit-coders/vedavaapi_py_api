import vedavaapi_data.schema.ullekhanam as backend_data_containers
import vedavaapi_data
import vedavaapi_data.schema.common as common_data_containers
import flask_restplus
from flask import Blueprint

URL_PREFIX = '/v1'
api_blueprint = Blueprint(name='ullekhanam_api', import_name=__name__)
api = flask_restplus.Api(app=api_blueprint, version='1.0', title='vedavaapi py API',
                         description='vedavaapi py API. Report issues <a href="https://github.com/vedavaapi/vedavaapi_py_api">here</a>. '
                                     'For a list of JSON schema-s this API uses (referred to by name in docs) see <a href="schemas"> here</a>. <BR>'
                                     'A list of REST and non-REST API routes avalilable on this server: <a href="../sitemap">sitemap</a>.  ',
                         prefix=URL_PREFIX, doc='/docs')



@api_blueprint.route('/schemas')
def list_schemas():
  """???."""
  schemas = {
    "JsonObject": common_data_containers.JsonObject.schema,
    "JsonObjectNode": common_data_containers.JsonObjectNode.schema,
    "BookPortion": vedavaapi_data.schema.books.BookPortion.schema,
    "ImageAnnotation": backend_data_containers.ImageAnnotation.schema,
    "TextAnnotation": backend_data_containers.TextAnnotation.schema,
  }
  from flask.json import jsonify
  return jsonify(schemas)
