import logging

# Encapsulates the main database.

from cloudant.database import CouchDatabase
from pymongo.collection import Collection
from sanskrit_data.schema.ullekhanam import TextAnnotation
from sanskrit_data.schema.books import BookPortion
from vedavaapi_py_api.ullekhanam.backend.db import collections

import os

dbs = {}


def add_db(db, db_name_frontend="ullekhanam", external_file_store=None):
  logging.info("Initializing database")
  logging.info(db.__class__)
  ullekhanam_db = None
  if isinstance(db, CouchDatabase):
    from vedavaapi_py_api.ullekhanam.backend.db.collections import BookPortionsCouchdb
    ullekhanam_db = BookPortionsCouchdb(some_collection=db, db_name_frontend=db_name_frontend, external_file_store=external_file_store)
  elif isinstance(db, Collection):
    from vedavaapi_py_api.ullekhanam.backend.db.collections import BookPortionsMongodb
    ullekhanam_db = BookPortionsMongodb(some_collection=db, db_name_frontend=db_name_frontend, external_file_store=external_file_store)

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
  dbs[db_name_frontend] = ullekhanam_db

  # Add filestores for use with the DB.
  if external_file_store is not None:
    logging.info("Initializing work directory ...")
    os.makedirs(name=external_file_store, exist_ok=True)
    ullekhanam_db.import_all(rootdir=external_file_store)


# Directly accessing the module variable seems to yield spurious None values.
def get_db(db_name_frontend="ullekhanam"):
  if db_name_frontend in dbs:
    return dbs[db_name_frontend]
  else:
    return None


def get_file_store(db_name_frontend="ullekhanam"):
  if db_name_frontend in dbs:
    return dbs[db_name_frontend].external_file_store
  else:
    return None
