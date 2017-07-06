import logging
from bson import ObjectId

from common.db import DbInterface

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

def get_mongo_client(host):
  try:
    from pymongo import MongoClient
    return MongoClient(host=host)
  except Exception as e:
    print("Error initializing MongoDB database; aborting.", e)
    import sys
    sys.exit(1)

class Collection(DbInterface):
  def __init__(self, some_collection):
    logging.info("Initializing collection :" + str(some_collection))
    self.mongo_collection = some_collection

  def find_by_id(self, id):
    return self.mongo_collection.find_one({"_id": ObjectId(id)})

  def find(self, filter):
    return self.mongo_collection.find(filter=filter)

  def find_one(self, filter):
    return self.mongo_collection.find_one(filter=filter)

  def get_targetting_entities(self, json_obj, entity_type=None):
    filter = {
      "targets": {
        "$elemMatch": {
          "container_id": str(json_obj._id)
        }
      }
    }
    if entity_type:
      import common
      filter[common.TYPE_FIELD] = entity_type
    targetting_objs = [json_obj.make_from_dict(item) for item in self.mongo_collection.find(filter)]
    return targetting_objs

  def update_doc(self, doc):
    import common
    from pymongo import ReturnDocument
    doc.set_type_recursively()
    if hasattr(doc, "schema"):
      doc.validate_schema()

    map_to_write = doc.to_json_map()
    if hasattr(doc, "_id"):
      filter = {"_id": ObjectId(self._id)}
      map_to_write.pop("_id", None)
    else:
      filter = doc.to_json_map()

    updated_doc = self.mongo_collection.find_one_and_update(filter, {"$set": map_to_write}, upsert=True,
                                                            return_document=ReturnDocument.AFTER)
    doc.set_type()
    updated_doc[common.data_containers.TYPE_FIELD] = getattr(doc, common.data_containers.TYPE_FIELD)
    from common.data_containers import JsonObject
    return JsonObject.make_from_dict(updated_doc)

  def delete_doc(self):
    assert hasattr(self, "_id"), "_id not present!"
    return self.mongo_collection.delete_one({"_id": ObjectId(self._id)})

  def get_no_target_entities(self):
    iter = self.mongo_collection.find(
      filter={"$or":
                [{"targets" : {"$exists" : False}},
                 {"targets" : {"$size" : 0}}]
              },
      some_collection=self.db_collection)
    from common.data_containers import JsonObject
    return [JsonObject.make_from_dict(x) for x in iter]


