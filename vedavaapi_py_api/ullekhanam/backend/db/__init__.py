import logging

# Encapsulates the main database.

from cloudant.database import CouchDatabase
from pymongo.collection import Collection

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
  ullekhanam_db.add_index(keys_dict={
    "targets.container_id": 1
  }, index_name="targets_container_id")
  global dbs
  dbs[db_name] = ullekhanam_db


# Directly accessing the module variable seems to yield spurious None values.
def get_db(db_name="ullekhanam"):
  if db_name in dbs:
    return dbs[db_name]
  else:
    return None
