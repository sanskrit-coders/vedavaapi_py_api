import logging
from pymongo.database import Database

from textract.backend.db import DBWrapper
from textract.backend.db.collections import BookPortionsInterface, AnnotationsInterface
from common.db.mongodb import Collection

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class BookPortions(Collection, BookPortionsInterface): pass
class Annotations(Collection, AnnotationsInterface): pass

class MongoDbWrapper(DBWrapper):
  def __init__(self, dbname, client):
    self.dbname = dbname
    self.client = client
    self.initialize()

  def initialize(self):
    self.db = self.client[self.dbname]
    if not isinstance(self.db, Database):
      raise TypeError("database must be an instance of Database")
    self.books = BookPortions(self.db['book_portions'])
    self.annotations = Annotations(self.db['annotations'])

  def reset(self):
    logging.info("Clearing IndicDocs database")
    self.client.drop_database(self.dbname)
    self.initialize()


