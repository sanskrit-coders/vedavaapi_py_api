import logging

# Encapsulates the main database.

ullekhanam_db = None

def initdb(db):
  logging.info("Initializing database")
  global ullekhanam_db
  from vedavaapi_py_api.ullekhanam.backend.db.collections import BookPortionsCouchdb
  ullekhanam_db =  BookPortionsCouchdb(db)


def get_db():
  return ullekhanam_db