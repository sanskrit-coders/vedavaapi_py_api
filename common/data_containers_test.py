import logging
import os
import unittest

import common
import data_containers

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class TestDBRoundTrip(unittest.TestCase):
  def test_JsonObjectNode(self):
    from textract.backend.mongodb import DBWrapper
    test_db = DBWrapper(dbname="test_db", client=common.get_mongo_client())
    CODE_ROOT = os.path.dirname(os.path.dirname(__file__))
    self.test_db.importAll(os.path.join(CODE_ROOT, "textract/example-repo"))
    book = common.data_containers.JsonObject.find_one(some_collection=self.test_db.books.db_collection, filter={"path": "kannada/skt-dict"})
    logging.debug(str(book))
    json_node = common.data_containers.JsonObjectNode.from_details(content=book)
    json_node.fill_descendents(self.test_db.books.db_collection)
    logging.debug(str(json_node))
    self.assertEquals(json_node.children.__len__(), 11)


if __name__ == '__main__':
  unittest.main()
