from __future__ import absolute_import

import logging
import os
import unittest

from sanskrit_data.schema.common import JsonObject, JsonObjectNode

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class TestDBRoundTrip(unittest.TestCase):
  def test_JsonObjectNode(self):
    from sanskrit_data.db.mongodb import get_mongo_client
    import common
    common.set_configuration()
    server_config = common.server_config
    from ullekhanam.backend import db as backend_db
    backend_db.initdb(dbname="test_db", client=get_mongo_client(server_config["mongo_host"]))
    self.test_db = backend_db.textract_db
    CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    self.test_db.importAll(os.path.join(CODE_ROOT, "textract/example-repo"))
    book = JsonObject.make_from_dict(self.test_db.books.find_one(filter={"path": "english"}))
    logging.debug(str(book))
    json_node = JsonObjectNode.from_details(content=book)
    json_node.fill_descendents(self.test_db.books)
    logging.debug(str(json_node))
    self.assertEquals(json_node.children.__len__(), 3)


if __name__ == '__main__':
  unittest.main()
