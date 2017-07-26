from __future__ import absolute_import

import logging

from common.db import DbInterface

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class Database(DbInterface):
  def __init__(self, db):
    logging.info("Initializing collection :" + str(db))
    self.db = db

  def update_doc(self, doc):
    super(Database, self).update_doc(doc=doc)
    if not hasattr(doc, "_id"):
      from uuid import uuid4
      doc._id = uuid4().hex
    map_to_write = doc.to_json_map()
    saved_id = self.db.save(map_to_write)
    assert saved_id == doc._id
    return doc

  def delete_doc(self, doc):
    assert hasattr(doc, "_id")
    map_to_delete = doc.to_json_map()
    self.db.delete(map_to_delete)

  def find_by_indexed_key(self, index_name, key):
    raise Exception("not implemented")
    pass

  # filter: A javascript boolean valued function.
  def find(self, filter_fn):
    map_fun = '''function(doc) {
     filterFn = %(filter);
     if (filterFn(doc)) emit(1);}'''.format(filter)
    logging.debug(map_fun)
    for row in self.db.query(map_fun):
      yield row.doc

  def get_targetting_entities(self, json_obj, entity_type=None):
    raise Exception("not implemented")
    pass
