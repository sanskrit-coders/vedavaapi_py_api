from __future__ import absolute_import

import logging
import unittest

import couchdb
import os
from couchdb import Server

import common
from common.db.couchdb import Database
from sanskrit_data.schema.common import JsonObject, JsonObjectNode

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
    updated_doc.xyz = "xyzvalue"
    updated_doc = self.test_db.update_doc(doc)
    logging.debug(updated_doc)
    pass

  def test_delete_doc_find_by_id(self):
    doc = JsonObject()
    updated_doc = self.test_db.update_doc(doc)
    logging.debug(updated_doc)
    self.test_db.delete_doc(doc)
    self.assertEqual(self.test_db.find_by_id(updated_doc._id), None)
    self.test_db.delete_doc(doc)

  def test_find(self):
    doc = JsonObject()
    doc.xyz = "xyzvalue"
    updated_doc = self.test_db.update_doc(doc)
    logging.debug(updated_doc)
    found_doc = self.test_db.find(filter={"xyz": "xyzvalue"}).next()
    self.assertEqual(str(updated_doc), str(found_doc))


if __name__ == '__main__':
  unittest.main()