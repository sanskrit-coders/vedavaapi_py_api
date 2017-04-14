from bson import ObjectId

class JsonObject:
  def __eq__(self, other):
    return self.__dict__ == other.__dict__

  def equals_ignore_id(self, other):
    dict1 = self.__dict__
    dict1.remove("_id")
    dict2 = other.__dict__
    dict2.remove("_id")
    return dict1 == dict2


class Target(JsonObject):
  def __init__(self, container_id):
    self.container_id = container_id

class BookPortion(JsonObject):

  @classmethod
  def from_details(cls, title, authors, path):
    book_portion = BookPortion()
    book_portion.class_type = str(cls.__name__)
    book_portion.title = title
    book_portion.authors = authors
    book_portion.path = path
    book_portion.targets = []
    return book_portion

  @classmethod
  def from_dict(cls, dict):
    book_portion = BookPortion()
    [setattr(book_portion, key, dict[key]) for key in dict]
    return book_portion
