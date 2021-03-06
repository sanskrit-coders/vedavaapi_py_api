"""
This module defines the basic flask app, and sets it up.

It also defines some basic handlers.
"""

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
CORS(app=app,
     # injects the `Access-Control-Allow-Credentials` header in responses. This allows cookies and credentials to be submitted across domains.
     supports_credentials=True)

app.config.update(
  DEBUG=True,

  # Used to encrypt session cookies.
  SECRET_KEY=b64encode(os.urandom(24)).decode('utf-8'),

  SESSION_COOKIE_NAME="vedavaapi_session",
)


@app.route('/')
def index():
  flask.session['logstatus'] = 1
  return flask.redirect('static/api_docs_index.html')


# Cant use flask-sitemap - won't list flask restplus routes.
@app.route("/sitemap")
def site_map():
  output = []
  for rule in app.url_map.iter_rules():
    options = {}
    for arg in rule.arguments:
      options[arg] = "[{0}]".format(arg)

    methods = ','.join(rule.methods)
    url = str(rule)
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
