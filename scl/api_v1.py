import copy
import traceback
from collections import OrderedDict
from flask import Blueprint
from os.path import join

import flask
import jsonpickle

import flask_restplus
import logging
from flask_login import current_user
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

import common.data_containers as common_data_containers

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

URL_PREFIX = '/v1'
api_blueprint = Blueprint(name='scl_api', import_name=__name__)
api = flask_restplus.Api(app=api_blueprint, version='1.0', title='vedavaapi SCL py API',
                         description='vedavaapi SCL py API. Report issues <a href="https://github.com/vedavaapi/vedavaapi_py_api">here</a>. '
                                     'For a list of JSON schema-s this API uses (referred to by name in docs) see <a href="/scl/schemas"> here</a>. <BR>'
                                     'A list of REST and non-REST API routes avalilable on this server: <a href="/sitemap">/sitemap</a>.  ',
                         prefix=URL_PREFIX, doc='/docs')


