import logging

from sanskrit_data.db.mongodb import Collection

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

users_db = None

class Users(Collection): pass
