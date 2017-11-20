import logging

from sanskrit_data.db import DbInterface, mongodb
from sanskrit_data.schema.users import User

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class UsersInterface(DbInterface):
  """Operations on User objects in an Db"""

  def get_user_from_auth_info(self, auth_info):
    """Get a user object matching details in a certain AuthenticationInfo object."""
    user_dict = self.find_one(find_filter={"authentication_infos.auth_user_id": auth_info.auth_user_id,
                                           "authentication_infos.auth_provider": auth_info.auth_provider,
                                           })
    if user_dict is None:
      return None
    else:
      user = User.make_from_dict(user_dict)
      return user

  def get_matching_users_by_auth_infos(self, user):
    # Check to see if there are other entries in the database with identical authentication info.
    matching_users = []
    for auth_info in user.authentication_infos:
      matching_user = self.get_user_from_auth_info(auth_info=auth_info)
      if matching_user is not None:
        matching_users.append(matching_user)
    return matching_users


class UsersMongodb(mongodb.Collection, UsersInterface):
  def __init__(self, some_collection):
    super(UsersMongodb, self).__init__(some_collection=some_collection, db_name_frontend="users")


from sanskrit_data.db.couchdb import CloudantApiDatabase


class UsersCouchdb(CloudantApiDatabase, UsersInterface):
  def __init__(self, some_collection):
    super(UsersCouchdb, self).__init__(db=some_collection)


users_db = None
default_permissions = None

def setup(db, initial_users=None, default_permissions_in=None):
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

  # Add initial users to the users db if they don't exist.
  logging.info("Add initial users to the users db if they don't exist.")
  if initial_users is not None:
    for initial_user_dict in initial_users:
      initial_user = User.make_from_dict(initial_user_dict)
      matching_users = users_db.get_matching_users_by_auth_infos(user=initial_user)
      if len(matching_users) == 0:
        logging.info("Adding: " + str(initial_user))
        users_db.update_doc(initial_user_dict)
      else:
        logging.info("Not adding: " + str(initial_user))

  global default_permissions
  default_permissions = default_permissions_in

# Directly accessing the module variable seems to yield spurious None values.
def get_db():
  return users_db

def get_default_permissions():
  return default_permissions