# An API corresponding to SCL (samvit) software from UoHyd.

import logging

from common import file_helper

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

_DBNAME = "vedavaapi_scl_db"

scl_path = ""

def get_full_path(relative_path):
  from os.path import join
  return join(scl_path, relative_path)


def analyze_api(parms):
  outstr = file_helper.run_command("{} {} {} LOCAL json".format( \
    get_full_path("SHMT/prog/morph/callmorph.pl"), parms['word'], \
    'WX'), out_encoding = 'WX')
  import json
  o = json.loads(outstr)
  return o

def setup_app(params, server_config):
  global scl_path
  scl_path = server_config['scl_path']
  pass