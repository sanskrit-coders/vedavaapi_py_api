#!/usr/bin/python3 -u

# This web app may be run in two modes. See bottom of the file.

import getopt
# from flask.ext.cors import CORS
import logging
import os.path
import sys

from sanskrit_data.schema.common import JsonObject

# Add parent directory to PYTHONPATH, so that vedavaapi_py_api module can be found.
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
print(sys.path)

from vedavaapi_py_api import common, textract, ullekhanam
from vedavaapi_py_api.common import file_helper
from vedavaapi_py_api.common.flask_helper import app

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

params = JsonObject()

params.set_from_dict({
  'reset': False,
  'dbreset': False,
  'dbgFlag': False,
  'myport': 9000,
})

def setup_app():
  common.set_configuration(config_file_name=os.path.join(os.path.dirname(__file__), 'server_config_local.json'))
  server_config = common.server_config

  client = None
  if server_config["db"]["db_type"] == "couchdb":
    from sanskrit_data.db import couchdb
    client = couchdb.CloudantApiClient(url=server_config["db"]["couchdb_host"])
  elif server_config["db"]["db_type"] == "mongo":
    from sanskrit_data.db import mongodb
    client = mongodb.Client(url=server_config["db"]["mongo_host"])

  from vedavaapi_py_api import users
  from vedavaapi_py_api.users import users_api_v1
  users.setup(db=client.get_database_interface(db_name=server_config["db"]["users_db_name"]))
  ullekhanam_db = client.get_database(db_name=server_config["db"]["ullekhanam_db_name"])
  textract.setup_app(db=ullekhanam_db)

  logging.info("Root path: " + app.root_path)
  logging.info(app.instance_path)
  import vedavaapi_py_api.ullekhanam.api_v1
  import vedavaapi_py_api.textract.api_v1
  app.register_blueprint(users_api_v1.api_blueprint, url_prefix="/oauth")
  app.register_blueprint(textract.api_v1.api_blueprint, url_prefix="/textract")
  app.register_blueprint(ullekhanam.api_v1.api_blueprint, url_prefix="/ullekhanam")


def main(argv):
  def usage():
    logging.info("run.py [-r] [-R] [-d] [-o <workdir>] [-l <local_wloads_dir>] <repodir1>[:<reponame>] ...")
    exit(1)

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
  # noinspection PyUnboundLocalVariable
  params.repos = args

  setup_app()

  logging.info("Available on the following URLs:")
  for line in file_helper.run_command(["/sbin/ifconfig"]).split("\n"):
    import re
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
  logging.info("Running in stand-alone mode.")
  main(sys.argv[1:])
else:
  logging.info("Likely running as a WSGI app.")
  setup_app()
