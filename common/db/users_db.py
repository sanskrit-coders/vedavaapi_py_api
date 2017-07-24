from common.db.mongodb import Collection
import logging
logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

users_db = None

class Users(Collection): pass

def initialize_mongodb(client, users_db_name):
  global users_db
  db = client[users_db_name]
  from pymongo.database import Database
  if not isinstance(db, Database):
    raise TypeError("database must be an instance of Database")
  users_db = Users(db[users_db_name])
