import logging
from base64 import b64encode

import flask
import os
from flask_login import LoginManager

app = flask.Flask("vedavaapi")
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
  return flask.render_template('/textract/listBooks.html', title='Home')


@app.route('/guestlogin', methods=['GET', 'POST'])
def guestlogin():
  logging.info("Login using Guest....\n")
  email = flask.request.args.get('usermail')
  logging.info("email=" + str(email))
  flask.session['logstatus'] = 1
  return flask.render_template('/textract/listBooks.html', title='Home')


@app.route('/ui/<path:filepath>')
def fill_template(filepath):
  if 'logstatus' in flask.session:
    if flask.session['logstatus'] == 1:
      return flask.render_template(filepath)
    else:
      return flask.redirect('/')
  else:
    return flask.redirect('/')


@app.route('/static/<path:filepath>')
def static_file(filepath):
  return app.send_static_file('/static/' + filepath)

