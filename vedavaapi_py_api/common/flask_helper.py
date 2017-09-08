import logging
from base64 import b64encode

import flask
import jsonpickle
import os
from flask import url_for
from flask_cors import CORS

""" The flask app we serve in run.py.
"""
app = flask.Flask(
  # We pass the root module name - sets root directory.
  import_name="vedavaapi_py_api.run")

# Let Javascsipt hosted elsewhere access our API.
CORS(app)

# TODO: Set SECRET_KEY from server_config_local.
app.config.update(
  DEBUG=True,

  # Used to encrypt session cookies.
  SECRET_KEY=b64encode(os.urandom(24)).decode('utf-8'),

  SESSION_COOKIE_NAME="vedavaapi_session",
  # SERVER_NAME="localhost:9000",
)


@app.route('/')
def index():
  flask.session['logstatus'] = 1
  return flask.redirect('static/v0/html/listbooks.html')


@app.route('/ui/<path:filepath>')
def fill_template(filepath):
  if 'logstatus' in flask.session:
    if flask.session['logstatus'] == 1:
      from jinja2 import TemplateNotFound
      try:
        return flask.render_template(filepath)
      except TemplateNotFound as e:
        import traceback
        traceback.print_exc(e)
        flask.abort(404)
    else:
      return flask.redirect(url_for(endpoint='.index'))
  else:
    return flask.redirect(url_for(endpoint='.index'))


@app.route("/sitemap")
def site_map():
  output = []
  for rule in app.url_map.iter_rules():

    options = {}
    for arg in rule.arguments:
      options[arg] = "[{0}]".format(arg)

    methods = ','.join(rule.methods)
    url = url_for(rule.endpoint, **options)
    import urllib.request

    line = urllib.request.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
    output.append(line)

  logging.info(str(output))
  response = app.response_class(
    response=jsonpickle.dumps(output),
    status=200,
    mimetype='application/json'
  )
  return response
