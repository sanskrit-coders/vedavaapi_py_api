import logging

import sys
from pymongo.database import Database

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

scl_db = None

# Encapsulates the main database.
class DBWrapper:
  def __init__(self, dbname, client):
    self.dbname = dbname
    self.client = client
    self.initialize()

  #        if not database.write_concern.acknowledged:
  #            raise ConfigurationError('database must use '
  #                                     'acknowledged write_concern')

  def initialize(self):
    try:
      self.db = self.client[self.dbname]
      if not isinstance(self.db, Database):
        raise TypeError("database must be an instance of Database")
    except Exception as e:
      print("Error initializing MongoDB database; aborting.", e)
      sys.exit(1)


def initdb(dbname, server_config, reset=False):
  logging.info("Initializing database")
  global scl_db
  scl_db = DBWrapper(dbname, server_config)
  if reset:
    scl_db.reset()


def get_db():
  return scl_db
