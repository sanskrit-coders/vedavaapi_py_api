#!/usr/bin/python -u

# This web app may be run in two modes. See bottom of the file.

import getopt
# from flask.ext.cors import CORS
import logging
import sys

from sanskrit_data.schema import common

import textract.api_v1

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

params = common.JsonObject()

params.set_from_dict({
  'reset': False,
  'dbreset': False,
  'dbgFlag': False,
  'myport': 9000,
})

from common.flask_helper import app

def setup_app():
  import common
  common.set_configuration()
  server_config = common.server_config
  from common.db import mongodb
  from common.db import users_db
  users_db.initialize_mongodb(client = mongodb.get_mongo_client(host=server_config["mongo_host"]), users_db_name=server_config["users_db_name"])
  textract.setup_app(params, mongodb.get_mongo_client(host=server_config["mongo_host"]))
  logging.info("Root path: " + app.root_path)
  logging.info(app.instance_path)
  import ullekhanam.api_v1
  from common import users_api_v1
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
  params.repos = args

  setup_app()

  logging.info("Available on the following URLs:")
  import common
  for line in common.file_helper.run_command(["/sbin/ifconfig"]).split("\n"):
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
