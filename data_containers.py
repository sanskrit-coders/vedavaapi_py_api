# -*- coding: utf-8 -*-
import logging

import jsonpickle
from bson import ObjectId, json_util

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TYPE_FIELD = "py/object"

class JsonObject:
  def __init__(self):
    # self.class_type = str(self.__class__.__name__)
    setattr(self, TYPE_FIELD, self.__class__.__name__)

  def __str__(self):
    return str(self.__dict__)

  # This does not work as of 20170418
  @classmethod
  def make_from_dict_jsonpickle(cls, input_dict):
    obj = jsonpickle.decode(json_util.dumps(input_dict))
    logging.info(obj)

  @classmethod
  def make_from_dict(cls, input_dict):
    obj = JsonObject()
    logging.debug(input_dict)
    if input_dict.get(TYPE_FIELD) == "Target":
      obj = Target()
    elif input_dict.get(TYPE_FIELD) == "ImageTarget":
      obj = ImageAnnotation.ImageTarget()
    elif input_dict.get(TYPE_FIELD) == "Source":
      obj = Annotation.Source()
    elif input_dict.get(TYPE_FIELD) == "BookPortion":
      obj = BookPortion()
    elif input_dict.get(TYPE_FIELD) == "Annotation":
      obj = Annotation()
    elif input_dict.get(TYPE_FIELD) == "ImageAnnotation":
      obj = ImageAnnotation()
    elif input_dict.get(TYPE_FIELD) == "TextAnnotation":
      obj = TextAnnotation()
    else:
      logging.error("Unknown TYPE_FIELD " + input_dict.get(TYPE_FIELD))
    obj.set_from_dict(input_dict)
    return obj


  def set_from_dict(self, input_dict):
    for key, value in input_dict.iteritems():
      if isinstance(value, list):
        setattr(self, key, [JsonObject.make_from_dict(item) if isinstance(item, dict) else item for item in value])
      elif isinstance(value, dict):
        setattr(self, key, JsonObject.make_from_dict(value))
      else:
        setattr(self, key, value)

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
  @classmethod
  def from_details(cls, container_id):
    target = Target()
    target.container_id = container_id
    return target


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
    @classmethod
    def from_details(cls, container_id, x1=-1, y1=-1, x2=-1, y2=-1):
      target = ImageAnnotation.ImageTarget()
      target.container_id = container_id
      target.x1 = x1
      target.y1 = y1
      target.x2 = x2
      target.y2 = y2
      return target

  @classmethod
  def from_details(cls, targets, source):
    annotation = ImageAnnotation()
    annotation.set_base_details(targets, source)
    return annotation

class TextContent(JsonObject):
  @classmethod
  def from_details(cls, text, language = "UNK", encoding = "UNK"):
    text_content = TextContent()
    text_content.text = text
    text_content.language = language
    text_content.encoding = encoding
    return text_content


class TextAnnotation(Annotation):

  @classmethod
  def from_details(self, targets, source, content):
    annotation = TextAnnotation()
    annotation.set_base_details(targets, source)
    annotation.content = content
    return annotation
