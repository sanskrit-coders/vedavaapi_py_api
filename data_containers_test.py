import unittest
import data_containers
import jsonpickle
import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class TestJsonConversion(unittest.TestCase):

  def test_serialize_BookPortion(self):
    book_portion = data_containers.BookPortion(title="halAyudhakoshaH", authors=["halAyudhaH"])
    json = jsonpickle.encode(book_portion)
    logging.info(json)

    # TODO: fix below.
    self.assertEqual('foo'.upper(), 'FOO')

if __name__ == '__main__':
  unittest.main()