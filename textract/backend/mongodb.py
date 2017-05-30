import logging
import re
import sys
from pymongo.database import Database

import os
from pymongo import MongoClient

import common.data_containers
from common.config import run_command
from textract.backend import data_containers
from textract.backend.collections import BookPortions, Annotations, Users

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

__indicdocs_db = None

# Encapsulates the main database.
class DBWrapper:
  def __init__(self, dbname, server_config):
    self.dbname = dbname
    self.server_config = server_config
    self.initialize()

  #        if not database.write_concern.acknowledged:
  #            raise ConfigurationError('database must use '
  #                                     'acknowledged write_concern')

  def initialize(self):
    try:
      self.client = MongoClient(host=self.server_config["mongo_host"])
      self.db = self.client[self.dbname]
      if not isinstance(self.db, Database):
        raise TypeError("database must be an instance of Database")
      self.books = BookPortions(self.db['book_portions'])
      self.annotations = Annotations(self.db['annotations'])
      self.users = Users(self.db['users'])
    except Exception as e:
      print("Error initializing MongoDB database; aborting.", e)
      sys.exit(1)

  def reset(self):
    logging.info("Clearing IndicDocs database")
    self.client.drop_database(self.dbname)
    self.initialize()

  def importAll(self, rootdir, pattern=None):
    logging.info("Importing books into database from " + rootdir)
    cmd = "find " + rootdir + " \( \( -path '*/.??*' \) -prune \) , \( -path '*book_v2.json' \) -follow -print; true"
    logging.info(cmd)
    try:
      results = run_command(cmd)
    except Exception as e:
      logging.error("Error in find: " + str(e))
      return 0

    nbooks = 0

    for f in results.split("\n"):
      if not f:
        continue
      bpath, fname = os.path.split(f.replace(rootdir + "/", ""))
      logging.info("    " + bpath)
      if pattern and not re.search(pattern, bpath, re.IGNORECASE):
        continue
      book = data_containers.BookPortion.from_path(path=bpath, collection=self.books.db_collection)
      if book:
        logging.info("Book already present %s" % bpath)
      else:
        book_portion_node = common.data_containers.JsonObject.read_from_file(f)
        logging.info("Importing afresh! %s " % book_portion_node)
        book_portion_node.update_collection(self.books.db_collection)
        logging.debug(str(book_portion_node))
        nbooks = nbooks + 1
    return nbooks


def initdb(dbname, server_config, reset=False):
  global __indicdocs_db
  logging.info("Initializing database")
  __indicdocs_db = DBWrapper(dbname, server_config)
  if reset:
    __indicdocs_db.reset()


def get_db():
  return __indicdocs_db
