import logging

# Encapsulates the main database.

from cloudant.database import CouchDatabase
from pymongo.collection import Collection
from sanskrit_data.schema.ullekhanam import TextAnnotation
from sanskrit_data.schema.books import BookPortion
from vedavaapi_py_api.ullekhanam.backend.db import collections

dbs = {}


def add_db(db, db_name="ullekhanam"):
  logging.info("Initializing database")
  logging.info(db.__class__)
  ullekhanam_db = None
  if isinstance(db, CouchDatabase):
    from vedavaapi_py_api.ullekhanam.backend.db.collections import BookPortionsCouchdb
    ullekhanam_db = BookPortionsCouchdb(db)
  elif isinstance(db, Collection):
    from vedavaapi_py_api.ullekhanam.backend.db.collections import BookPortionsMongodb
    ullekhanam_db = BookPortionsMongodb(db)

  ## General indices (corresponds to schema defined in schema.common).
  # Not really required since BookPortion index creation automatically includes the below.
  # JsonObject.add_indexes(db_interface=ullekhanam_db)
  # JsonObjectWithTarget.add_indexes(db_interface=ullekhanam_db)

  ## Book portion indices (corresponds to schema defined in schema.books).
  # Appropriate index use confirmed: https://trello.com/c/CHKgDABv/117-mongodb-index-array-of-array
  BookPortion.add_indexes(db_interface=ullekhanam_db)

  ## Annotation indices (corresponds to schema defined in schema.ullekhanam).
  TextAnnotation.add_indexes(db_interface=ullekhanam_db)

  global dbs
  dbs[db_name] = ullekhanam_db


# Directly accessing the module variable seems to yield spurious None values.
def get_db(db_name="ullekhanam"):
  if db_name in dbs:
    return dbs[db_name]
  else:
    return None
