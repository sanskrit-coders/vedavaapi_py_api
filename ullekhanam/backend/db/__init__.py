import logging
import re

import os

import vedavaapi_data
import vedavaapi_data.schema.books

# Encapsulates the main database.


textract_db = None


class DBWrapper(object):
  def initialize(self):
    pass

  def reset(self):
    pass

    #        if not database.write_concern.acknowledged:
    #            raise ConfigurationError('database must use '
    #                                     'acknowledged write_concern')
  def importAll(self, rootdir, pattern=None):
    logging.info("Importing books into database from " + rootdir)
    cmd = "find " + rootdir + " \( \( -path '*/.??*' \) -prune \) , \( -path '*book_v2.json' \) -follow -print; true"
    logging.info(cmd)
    try:
      from common.file_helper import run_command
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
      book = vedavaapi_data.schema.books.BookPortion.from_path(path=bpath, db_interface=self.books)
      if book:
        logging.info("Book already present %s" % bpath)
      else:
        book_portion_node = vedavaapi_data.schema.common.JsonObject.read_from_file(f)
        logging.info("Importing afresh! %s " % book_portion_node)
        from jsonschema import ValidationError
        try:
          book_portion_node.update_collection(self.books)
        except ValidationError as e:
          import traceback
          logging.error(e)
          logging.error(traceback.format_exc())
        logging.debug(str(book_portion_node))
        nbooks = nbooks + 1
    return nbooks

def initdb(dbname, client):
  logging.info("Initializing database")
  global textract_db
  from ullekhanam.backend.db.mongodb import MongoDbWrapper
  textract_db = MongoDbWrapper(dbname, client)


def get_db():
  return textract_db