from flask import make_response, json


def gen_response(status='ok', result=None):
  retobj = {'status': status}
  if not result is None:
    retobj['result'] = result
  return make_response(json.dumps(retobj))
  # return json.dumps(retobj)


def gen_error_response(msg):
  return make_response({'status': msg})
