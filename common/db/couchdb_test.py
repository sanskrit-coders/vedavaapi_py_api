from __future__ import absolute_import

import logging
import unittest

import couchdb
import os
from couchdb import Server

import common
from common.db.couchdb import Database
from vedavaapi_data.schema.common import JsonObject, JsonObjectNode

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class TestDBRoundTrip(unittest.TestCase):
  TEST_DB_NAME = 'vedavaapi_test'
  def setUp(self):
    common.set_configuration()
    self.server = Server(url=common.server_config["couchdb_host"])
    self.test_db_base = None
    try:
      self.test_db_base = self.server[self.TEST_DB_NAME]
    except:
      self.test_db_base = self.server.create(self.TEST_DB_NAME)
    self.test_db = Database(db=self.test_db_base)

  def tearDown(self):
    pass
    # self.server.delete(self.TEST_DB_NAME)

  def test_update_doc(self):
    doc = JsonObject()
    updated_doc = self.test_db.update_doc(doc)
    logging.debug(updated_doc)
    pass

if __name__ == '__main__':
  unittest.main()