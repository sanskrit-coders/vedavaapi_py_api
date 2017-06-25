#!/usr/bin/python -u

# This web app may be run in two modes. See bottom of the file.

import getopt
# from flask.ext.cors import CORS
import logging
import sys

import os

import common
import textract.api_v1
from common import data_containers
import oauth

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

params = data_containers.JsonObject()

params.set_from_dict({
  'reset': False,
  'dbreset': False,
  'dbgFlag': False,
  'myport': 9000,
})

server_config = data_containers.JsonObject()
config_file_name = os.path.join(os.path.dirname(__file__), 'server_config_local.json')
with open(config_file_name) as config_file:
  pickled_config = config_file.read()
  # logging.info(pickled_config)
  import jsonpickle
  server_config = jsonpickle.decode(pickled_config)

def get_mongo_client():
  try:
    from pymongo import MongoClient
    return MongoClient(host=server_config["mongo_host"])
  except Exception as e:
    print("Error initializing MongoDB database; aborting.", e)
    sys.exit(1)

mongo_client = get_mongo_client()
from common.flask_helper import app

def setup_app():
  textract.setup_app(params, mongo_client)
  logging.info("Root path: " + app.root_path)
  logging.info(app.instance_path)
  logging.info("Available on the following URLs:")
  app.register_blueprint(textract.api_v1.api_blueprint, url_prefix="/textract")

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
  for line in common.config.run_command(["/sbin/ifconfig"]).split("\n"):
    m = oauth.re.match('\s*inet addr:(.*?) .*', line)
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
