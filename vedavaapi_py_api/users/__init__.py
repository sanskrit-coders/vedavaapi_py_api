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
  users_db.add_index(keys_dict={
    "authentication_infos.auth_user_id" : 1
  }, index_name="authentication_infos.auth_user_id")


class Users(Collection): pass
