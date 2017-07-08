import logging
import unittest

import os

import common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class TestDBRoundTrip(unittest.TestCase):
  def test_JsonObjectNode(self):
    from textract.backend import db
    db.initdb(dbname="test_db", client=common.db.mongodb.get_mongo_client("mongodb://vedavaapiUser:vedavaapiAdmin@localhost/"))
    self.test_db = db.textract_db
    CODE_ROOT = os.path.dirname(os.path.dirname(__file__))
    self.test_db.importAll(os.path.join(CODE_ROOT, "textract/example-repo"))
    book = common.JsonObject.find_one(db_interface=self.test_db.books, filter={"path": "kannada/skt-dict"})
    logging.debug(str(book))
    json_node = common.JsonObjectNode.from_details(content=book)
    json_node.fill_descendents(self.test_db.books)
    logging.debug(str(json_node))
    self.assertEquals(json_node.children.__len__(), 11)


if __name__ == '__main__':
  unittest.main()
