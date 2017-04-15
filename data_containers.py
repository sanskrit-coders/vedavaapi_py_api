# -*- coding: utf-8 -*-
import logging
from bson import ObjectId

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class JsonObject:
  def __init__(self):
    self.class_type = str(self.__class__.__name__)

  def __str__(self):
    return str(self.__dict__)

  def set_from_dict(self, dict):
    [setattr(self, key, dict[key]) for key in dict]

  def set_from_id(self, collection, id):
    return self.set_from_dict(
      collection.find_one({"_id" : ObjectId(id)}))

  def toJsonMap(self):
    jsonMap = {}
    for key, value in self.__dict__.iteritems():
      if isinstance(value, JsonObject):
        jsonMap[key] = value.toJsonMap()
      elif isinstance(value, list):
        jsonMap[key] = [item.toJsonMap() if isinstance(item, JsonObject) else item for item in value]
      else:
        jsonMap[key] = value
    return jsonMap


  def equals_ignore_id(self, other):
    # Makes a unicode copy.
    def to_unicode(input):
      if isinstance(input, dict):
        return {key: to_unicode(value) for key, value in input.iteritems()}
      elif isinstance(input, list):
        return [to_unicode(element) for element in input]
      elif isinstance(input, unicode):
        return input.encode('utf-8')
      else:
        return input

    dict1 = to_unicode(self.toJsonMap())
    dict1.pop("_id", None)
    # logging.debug(self.__dict__)
    # logging.debug(dict1)
    dict2 = to_unicode(other.toJsonMap())
    dict2.pop("_id", None)
    # logging.debug(other.__dict__)
    # logging.debug(dict2)
    return dict1 == dict2


class Target(JsonObject):
  def __init__(self, container_id):
    self.container_id = container_id

class BookPortion(JsonObject):
  @classmethod
  def from_details(cls, title, authors, path, targets = []):
    book_portion = BookPortion()
    book_portion.title = title
    book_portion.authors = authors
    book_portion.path = path
    book_portion.targets = targets
    return book_portion

  @classmethod
  def from_path(cls, collection, path):
    book_portion = BookPortion()
    book_portion.set_from_dict(collection.find_one({"path" : path}))
    return book_portion

class Annotation(JsonObject):
  class Source(JsonObject):
    @classmethod
    def from_details(cls, type, id):
      source = Annotation.Source()
      source.type = type
      source.id = id
      return source

  def set_base_details(self, targets, source):
    self.targets = targets
    self.source = source

class ImageAnnotation(Annotation):
  class ImageTarget(Target):
    def __init__(self, container_id, x1=-1, y1=-1, x2=-1, y2=-1):
      Target.__init__(self, container_id=container_id)
      self.x1 = x1
      self.y1 = y1
      self.x2 = x2
      self.y2 = y2

  @classmethod
  def from_details(self, targets, source):
    annotation = ImageAnnotation()
    annotation.set_base_details(targets, source)
    return annotation
