from common.db.mongodb import Collection
import logging
logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

user_db = None

class Users(Collection): pass

def initialize_mongodb(self, client, users_db_name):
  global user_db
  self.db = client[users_db_name]
  from pymongo.database import Database
  if not isinstance(self.db, Database):
    raise TypeError("database must be an instance of Database")
  user_db = Users(self.db[users_db_name])


def get_db():
  return user_db