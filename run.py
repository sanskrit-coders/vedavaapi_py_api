#!/usr/bin/python -u
import getopt
# from flask.ext.cors import CORS
import logging
import sys

from flask import *

import common
import textract.api_v1
from common import data_containers
from oauth import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

params = data_containers.JsonObject()

params.set_from_dict({
  'reset': False,
  'dbreset': False,
  'dbgFlag': False,
  'myport': common.config.PORTNUM,
})

server_config = data_containers.JsonObject()

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



  with open('server_config_local.json') as config_file:
    pickled_config = config_file.read()
    # logging.info(pickled_config)
    import jsonpickle
    server_config = jsonpickle.decode(pickled_config)

  textract.setup_app(params, server_config)

  from common.flask_helper import app
  logging.info("Root path: " + app.root_path)
  logging.info(app.instance_path)
  logging.info("Available on the following URLs:")
  for line in common.config.run_command(["/sbin/ifconfig"]).split("\n"):
    m = re.match('\s*inet addr:(.*?) .*', line)
    if m:
      logging.info("    http://" + m.group(1) + ":" + str(params.myport) + "/")
  app.register_blueprint(textract.api_v1.api_blueprint, url_prefix="/textract")
  app.run(
    host="0.0.0.0",
    port=params.myport,
    debug=params.dbgFlag,
    use_reloader=False
  )

if __name__ == "__main__":
  main(sys.argv[1:])
else:
  textract.setup_app(params)
