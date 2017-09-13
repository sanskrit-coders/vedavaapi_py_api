import logging

from sanskrit_data.db import DbInterface, mongodb
from sanskrit_data.schema.users import User

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class UsersInterface(DbInterface):
  """Operations on User objects in an Db"""

  def get_user(self, auth_info):
    """Get a user object matching details in a certain AuthenticationInfo object."""
    user_dict = self.find_one(find_filter={"authentication_infos.auth_user_id": auth_info.auth_user_id,
                                      "authentication_infos.auth_provider": auth_info.auth_provider,
                                      })
    if user_dict is None:
      return None
    else:
      user = User.make_from_dict(user_dict)
      return user



class UsersMongodb(mongodb.Collection, UsersInterface):
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
  logging.info(db.__class__)
  from pymongo.collection import Collection
  if isinstance(db, CouchDatabase):
    users_db = UsersCouchdb(db)
  elif isinstance(db, Collection):
    users_db = UsersMongodb(db)
  users_db.add_index(keys_dict={
    "authentication_infos.auth_user_id": 1
  }, index_name="authentication_infos.auth_user_id")

# Directly accessing the module variable seems to yield spurious None values.
def get_db():
  return users_db