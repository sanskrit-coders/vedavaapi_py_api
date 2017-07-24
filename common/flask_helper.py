import logging
from base64 import b64encode

import flask
import jsonpickle
import os
from flask import url_for

# Pass the root module name - sets root directory.
app = flask.Flask("run")
app.config['SECRET_KEY'] = b64encode(os.urandom(24)).decode('utf-8')


@app.route('/')
def index():
  flask.session['logstatus'] = 1
  return flask.render_template('textract/listBooks.html', title='Home')


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
      return flask.redirect('/')
  else:
    return flask.redirect('/')


@app.route('/static/<path:filepath>')
def static_file(filepath):
  return app.send_static_file('static/' + filepath)


@app.route("/sitemap")
def site_map():
  output = []
  for rule in app.url_map.iter_rules():

    options = {}
    for arg in rule.arguments:
      options[arg] = "[{0}]".format(arg)

    methods = ','.join(rule.methods)
    url = url_for(rule.endpoint, **options)
    import urllib
    line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
    output.append(line)

  logging.info(str(output))
  response = app.response_class(
    response=jsonpickle.dumps(output),
    status=200,
    mimetype='application/json'
  )
  return response


