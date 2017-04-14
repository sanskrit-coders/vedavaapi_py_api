import unittest
import data_containers
import jsonpickle
import logging

from indicdocs import IndicDocs

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class TestDBRoundTrip(unittest.TestCase):
  test_db = IndicDocs("test_db")

  def test_BookPortion(self):
    book_portion = data_containers.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha")

    json = jsonpickle.encode(book_portion)
    logging.info("json pickle is " + json)

    book_portions = self.test_db.db.book_portions
    result = book_portions.update({"path" : book_portion.path}, book_portion.__dict__, upsert=True)
    logging.debug("update result is "  + str(result))

    book_portion_retrieved = data_containers.BookPortion.from_dict(
      book_portions.find_one({"path" : book_portion.path}))

    logging.info(str(book_portion.__dict__))
    logging.info(str(book_portion_retrieved.__dict__))
    # TODO: fix below.
    self.assertEqual(book_portion.equals_ignore_id(book_portion_retrieved))

if __name__ == '__main__':
  unittest.main()