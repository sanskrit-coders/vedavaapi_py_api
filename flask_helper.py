from bson import json_util

from flask import make_response


def gen_response(status='ok', result=None):
  retobj = {'status': status}
  if not result is None:
    retobj['result'] = result
  return make_response(json_util.dumps(retobj))
  # return json.dumps(retobj)


def gen_error_response(msg):
  return make_response({'status': msg})
