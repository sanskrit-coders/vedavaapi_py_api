#!/usr/bin/python -u
import datetime
import getopt
from base64 import b64encode
from sys import argv

from flask import *
from flask_login import LoginManager

import api_v1
# from flask.ext.cors import CORS
from backend import paths
from backend.collections import *
# from file import file_api
from backend.data_containers import User
from backend.db import initdb, get_db
from oauth import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

app = api_v1.app

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

lm = LoginManager(app)
lm.login_view = 'index'


@app.route('/')
def index():
  session['logstatus'] = 1
  return render_template('listBooks.html', title='Home')


@app.route('/guestlogin', methods=['GET', 'POST'])
def guestlogin():
  logging.info("Login using Guest....\n")
  email = request.args.get('usermail')
  logging.info("email=" + str(email))
  user = get_db().users.insert(
    {"nickname": "Guest", "email": str(email), "confirmed": True, "confirmed_on": str(datetime.datetime.now())})
  user = User(user['_id'], user['nickname'], user['email'], user['confirmed'])
  session['logstatus'] = 1
  return render_template('listBooks.html', title='Home')


@app.route('/ui/<filename>')
def fill_template(filename):
  if 'logstatus' in session:
    if session['logstatus'] == 1:
      return render_template(filename)
    else:
      return redirect('/')
  else:
    return redirect('/')


@app.route('/static/<path:filepath>')
def root(filepath):
  return app.send_static_file('/static/' + filepath)


@app.route('/relpath/<path:relpath>')
def send_file_relpath(relpath):
  return (send_from_directory(paths.DATADIR, relpath))


@app.route('/path/<path:relpath>')
def browsedir(relpath):
  fullpath = os.join(paths.DATADIR, relpath)
  logging.info(fullpath)
  return render_template("fancytree.html", abspath=fullpath)


# @app.route('/<path:abspath>')
# def details_dir(abspath):
#	logging.info("abspath:" + str(abspath))
#	return render_template("fancytree.html", abspath='/'+abspath)

@app.route('/dirtree/<path:abspath>')
def listdirtree(abspath):
  # print abspath
  data = list_dirtree("/" + abspath)
  # logging.info("Data:" + str(json.dumps(data)))
  return json.dumps(data)


(cmddir, cmdname) = os.path.split(argv[0])
logging.info("My path is " + os.path.abspath(cmddir))


def usage():
  logging.info(cmdname + " [-r] [-R] [-d] [-o <workdir>] [-l <local_wloads_dir>] <repodir1>[:<reponame>] ...")
  exit(1)


params = data_containers.JsonObject()

params.set_from_dict({
  'reset': False,
  'dbreset': False,
  'dbgFlag': False,
  'myport': PORTNUM,
})


def setup_app(params):
  logging.info(cmdname + ": Using " + paths.DATADIR)
  initdb(INDICDOC_DBNAME, params.dbreset)

  # Import all book metadata into the IndicDocs database
  paths.init_data_dir(params.reset)
  get_db().importAll(paths.DATADIR)


def main(argv):
  try:
    opts, args = getopt.getopt(argv, "do:l:p:rRh", ["workdir=", "wloaddir="])
  except getopt.GetoptError:
    usage()

  for opt, arg in opts:
    if opt == '-h':
      usage()
    elif opt in ("-o", "--workdir"):
      params.wdir = arg
    elif opt in ("-l", "--wloaddir"):
      params.localdir = arg
    elif opt in ("-p", "--port"):
      params.myport = int(arg)
    elif opt in ("-r", "--reset"):
      params.reset = True
    elif opt in ("-R", "--dbreset"):
      params.dbreset = True
    elif opt in ("-d", "--debug"):
      params.dbgFlag = True
  params.repos = args

  setup_app(params)

  logging.info("Available on the following URLs:")
  for line in run_command(["/sbin/ifconfig"]).split("\n"):
    m = re.match('\s*inet addr:(.*?) .*', line)
    if m:
      logging.info("    http://" + m.group(1) + ":" + str(params.myport) + "/")
  app.run(
    host="0.0.0.0",
    port=params.myport,
    debug=params.dbgFlag,
    use_reloader=False
  )


if __name__ == "__main__":
  main(sys.argv[1:])
else:
  setup_app(params)
