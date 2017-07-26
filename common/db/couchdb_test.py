from __future__ import absolute_import

import logging
import unittest

import os

from vedavaapi_data.schema.common import JsonObject, JsonObjectNode

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class TestDBRoundTrip(unittest.TestCase):
  def test_JsonObjectNode(self):
    pass


if __name__ == '__main__':
  unittest.main()