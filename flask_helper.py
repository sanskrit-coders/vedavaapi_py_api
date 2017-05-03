from bson import json_util

import flask

import common
from backend.data_containers import JsonObject


class JsonAjaxResponse(JsonObject):
  def __init__(self, status='ok', result=None):
    assert common.check_class(status, [str])
    self.status = status
    if result:
      assert common.check_class(result, [str, unicode, JsonObject])
      self.result = result

  def to_flask_response(self):
    return flask.make_response(str(self))


class JsonAjaxErrorResponse(JsonAjaxResponse):
  def __init__(self, status):
    JsonAjaxResponse.__init__(status=status)
