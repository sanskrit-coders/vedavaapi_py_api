import logging

import sys

from vedavaapi_data.schema import common
from vedavaapi_data.schema.common import JsonObject, recursively_merge, TYPE_FIELD, update_json_class_index

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class UserPermission(JsonObject):
  schema = recursively_merge(
    JsonObject.schema, {
      "properties": {
        TYPE_FIELD: {
          "enum": ["UserPermission"]
        },
        "service": {
          "type": "string",
          "enum": [".*", "ullekhanam"],
          "description": "Allowable values should be predetermined regular expressions."
        },
        "actions": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["read", "write", "admin"],
          },
          "description": "Should be an enum in the future."
        },
      },
    }
  )

  @classmethod
  def from_details(cls, service, actions):
    obj = UserPermission()
    obj.service = service
    obj.actions = actions
    return obj


class AuthenticationInfo(JsonObject):
  schema = recursively_merge(
    JsonObject.schema, {
      "properties": {
        TYPE_FIELD: {
          "enum": ["AuthenticationInfo"]
        },
        "auth_user_id": {
          "type": "string"
        },
        "auth_provider": {
          "type": "string"
        }
      }
    }
  )

  @classmethod
  def from_details(cls, auth_user_id, auth_provider):
    obj = AuthenticationInfo()
    obj.auth_user_id = auth_user_id
    obj.auth_provider = auth_provider
    return obj

class User(JsonObject):
  """Represents a user of our service."""
  schema = recursively_merge(
    JsonObject.schema, {
      "properties": {
        TYPE_FIELD: {
          "enum": ["User"]
        },
        "authentication_infos": {
          "type": "array",
          "items": AuthenticationInfo.schema,
        },
        "permissions": {
          "type": "array",
          "items": UserPermission.schema,
        },
      },
    }
  )

  @classmethod
  def from_details(cls, nickname, auth_user_id, auth_provider, permissions=None):
    obj = User()
    obj.authentication_infos = [AuthenticationInfo.from_details(auth_provider=auth_provider, auth_user_id=auth_user_id)]
    obj.nickname = nickname
    if permissions:
      obj.permissions = permissions
    return obj

  def check_permission(self, service, action):
    def fullmatch(pattern, string, flags=0):
      """Emulate python-3.4 re.fullmatch()."""
      import re
      return re.match("(?:" + pattern + r")\Z", string, flags=flags)

    for permission in self.permissions:
      if fullmatch(pattern=permission.service, string=service):
        for permitted_action in permission.actions:
          if fullmatch(pattern=permitted_action, string=action):
            return True
    return False

# Essential for depickling to work.
update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)
