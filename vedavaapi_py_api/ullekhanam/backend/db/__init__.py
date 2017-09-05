import logging

# Encapsulates the main database.

from cloudant.database import CouchDatabase
from pymongo.collection import Collection

from vedavaapi_py_api.ullekhanam.backend.db import collections

ullekhanam_db = None

def initdb(db):
  logging.info("Initializing database")
  global ullekhanam_db
  logging.info(db.__class__)
  if isinstance(db, CouchDatabase):
    from vedavaapi_py_api.ullekhanam.backend.db.collections import BookPortionsCouchdb
    ullekhanam_db =  BookPortionsCouchdb(db)
  elif isinstance(db, Collection):
    from vedavaapi_py_api.ullekhanam.backend.db.collections import BookPortionsMongodb
    ullekhanam_db =  BookPortionsMongodb(db)
  ullekhanam_db.add_index(keys_dict={
    "targets.container_id" : 1
  }, index_name="targets_container_id")



def get_db():
  return ullekhanam_db