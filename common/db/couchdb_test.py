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

common.set_configuration()
server = Server(url=common.server_config["couchdb_host"])
server.delete('vedavaapi_test')
test_db_base = server.create('vedavaapi_test')
test_db = Database(db=test_db_base)


class TestDBRoundTrip(unittest.TestCase):
  def test_update_doc(self):
    doc = JsonObject()
    updated_doc = test_db.update_doc(doc)
    logging.debug(updated_doc)
    pass


if __name__ == '__main__':
  unittest.main()