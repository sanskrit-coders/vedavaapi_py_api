import logging
from pymongo.database import Database

from common.db.mongodb import Collection
from ullekhanam.backend.db import DBWrapper
from ullekhanam.backend.db.collections import BookPortionsInterface

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class BookPortions(Collection, BookPortionsInterface): pass

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

  def reset(self):
    logging.info("Clearing IndicDocs database")
    self.client.drop_database(self.dbname)
    self.initialize()


