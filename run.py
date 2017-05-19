#!/usr/bin/python -u
import getopt
# from flask.ext.cors import CORS
import logging
import sys
from sys import argv

import jsonpickle
import os
from flask import *

import common
import textract.api_v1
from common import data_containers
from common.flask_helper import app
from oauth import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

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


def main(argv):
  def usage():
    logging.info("run.py [-r] [-R] [-d] [-o <workdir>] [-l <local_wloads_dir>] <repodir1>[:<reponame>] ...")
    exit(1)


  params = data_containers.JsonObject()

  params.set_from_dict({
    'reset': False,
    'dbreset': False,
    'dbgFlag': False,
    'myport': common.config.PORTNUM,
  })



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

  textract.setup_app(params)

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
