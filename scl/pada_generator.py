import json

import logging

import common.file_helper
from scl import get_full_path

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def noun_forms(root_wx, linga_wx):
  level = 1
  cmd = "{} {} {} {} {} {} LOCAL json".format(
    get_full_path("skt_gen/noun/gen_noun.pl"), root_wx,
    linga_wx, 'WX', 'WX', level)
  outstr = common.file_helper.run_command(cmd)
  logging.debug(outstr)
  return json.loads(outstr)
