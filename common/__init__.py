import logging

import common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def get_configuration():
  import os
  CODE_ROOT = os.path.dirname(os.path.dirname(__file__))
  from vedavaapi_data.schema import common
  server_config = common.JsonObject()
  config_file_name = os.path.join(CODE_ROOT, 'server_config_local.json')
  server_config = common.JsonObject.read_from_file(config_file_name)
  return server_config


def urlize(pathsuffix, text=None, newtab=True):
  tabclause = ""
  if newtab:
    tabclause = 'target="_blank"'
  if not text:
    text = pathsuffix
  return '<a href="/workloads/taillog/15/' + pathsuffix + '" ' + tabclause + '>' + text + '</a>'


