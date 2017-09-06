import logging

from sanskrit_data.db.mongodb import Collection

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

users_db = None

def setup(db):
  global users_db
  users_db = db


class Users(Collection): pass
