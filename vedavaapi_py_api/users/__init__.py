import logging

from sanskrit_data.db import DbInterface
from sanskrit_data.db.mongodb import Collection

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)



class UsersInterface(DbInterface):
  """Operations on User objects in an Db"""
  pass


from sanskrit_data.db.mongodb import Collection
class UsersMongodb(Collection, UsersInterface):
  def __init__(self, some_collection):
    super(UsersMongodb, self).__init__(some_collection=some_collection)


from sanskrit_data.db.couchdb import CloudantApiDatabase
class UsersCouchdb(CloudantApiDatabase, UsersInterface):
  def __init__(self, some_collection):
    super(UsersCouchdb, self).__init__(db=some_collection)


users_db = None

def setup(db):
  global users_db
  from cloudant.database import CouchDatabase
  if isinstance(db, CouchDatabase):
    from vedavaapi_py_api.ullekhanam.backend.db.collections import UsersCouchdb
    users_db =  UsersCouchdb(db)
  elif isinstance(db, Collection):
    from vedavaapi_py_api.ullekhanam.backend.db.collections import UsersMongodb
    users_db =  UsersMongodb(db)
  users_db = db
  users_db.add_index(keys_dict={
    "authentication_infos.auth_user_id" : 1
  }, index_name="authentication_infos.auth_user_id")
