import logging
from base64 import b64encode

import flask
import flask_restplus
import jsonpickle
import os
from flask import url_for
from flask_login import LoginManager

# Pass the root module name - sets root directory.
app = flask.Flask("run")
lm = LoginManager(app)

app.config['SECRET_KEY'] = b64encode(os.urandom(24)).decode('utf-8')
app.config['OAUTH_CREDENTIALS'] = {
  'facebook': {
    'id': '1706950096293019',
    'secret': '1b2523ac7d0f4b7a73c410b2ec82586c'
  },
  'twitter': {
    'id': 'jSd7EMZFTQlxjLFG4WLmAe2OX',
    'secret': 'gvkh9fbbnKQXXbnqxfs8C0tCEqgNKKzoYJAWQQwtMG07UOPKAj'
  }
}

lm.login_view = 'index'


@app.route('/')
def index():
  flask.session['logstatus'] = 1
  return flask.render_template('textract/listBooks.html', title='Home')


@app.route('/guestlogin', methods=['GET', 'POST'])
def guestlogin():
  logging.info("Login using Guest....\n")
  email = flask.request.args.get('usermail')
  logging.info("email=" + str(email))
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


@app.route('/users')
class UserListHandler(flask_restplus.Resource):
  def get(self):
    """Just list the users."""
    return "NOT IMPLEMENTED", 200


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


