import logging
import os
import re

import sanskrit_data
import sanskrit_data.schema.books

# Encapsulates the main database.
from sanskrit_data.db import DbInterface

ullekhanam_db = None

def initdb(db):
  logging.info("Initializing database")
  global ullekhanam_db
  from ullekhanam.backend.db.collections import BookPortionsMongodb
  ullekhanam_db =  BookPortionsMongodb(db)


def get_db():
  return ullekhanam_db