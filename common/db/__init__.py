
class DbInterface(object):

  def update_doc(self, doc):
    pass

  def delete_doc(self, doc):
    pass

  # Returns None if nothing is found.
  def find_by_id(self, id):
    pass

  # filter: A dict mapping field names to expected values.
  def find(self, filter):
    pass

  # Returns None if nothing is found.
  def find_one(self, filter):
    pass

  def get_targetting_entities(self, json_obj, entity_type=None):
    pass

  def get_no_target_entities(self):
    pass