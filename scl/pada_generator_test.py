import unittest

import logging

import jsonpickle

import pada_generator

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)
jsonpickle.set_encoder_options('simplejson', indent=2)


class PadaGeneratorTest(unittest.TestCase):
  def test_noun_forms(self):
    result = pada_generator.noun_forms(root_wx="rAma", linga_wx="pum")
    logging.info(jsonpickle.dumps(result))
    self.assertEqual(True, False)


if __name__ == '__main__':
  unittest.main()
