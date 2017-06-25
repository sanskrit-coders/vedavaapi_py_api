import unittest

import logging

import jsonpickle

import pada_generator
import run
from scl import setup_app

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)
jsonpickle.set_encoder_options('simplejson', indent=2)

setup_app(run.server_config)

class PadaGeneratorTest(unittest.TestCase):
  def test_noun_forms(self):
    result = pada_generator.noun_forms(root_wx="rAma", linga_wx="pum")
    logging.info(result)
    logging.info(jsonpickle.dumps(result))
    self.assertEqual(True, True)


if __name__ == '__main__':
  unittest.main()
