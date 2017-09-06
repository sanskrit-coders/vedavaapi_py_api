import json
import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

server_config = None

def set_configuration(config_file_name):
  global server_config
  with open(config_file_name) as fhandle:
    server_config = json.loads(fhandle.read())
