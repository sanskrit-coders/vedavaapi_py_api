# -*- coding: utf-8 -*-
import logging

import jsonpickle
from bson import ObjectId, json_util

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TYPE_FIELD = "py/object"


class JsonObject(object):
  def __init__(self):
    self.set_type()

  def set_type(self):
    # self.class_type = str(self.__class__.__name__)
    setattr(self, TYPE_FIELD, self.__module__ + "." + self.__class__.__name__)
    # setattr(self, TYPE_FIELD, self.__class__.__name__)

  def set_type_recursively(self):
    self.set_type()
    for key, value in self.__dict__.iteritems():
      if isinstance(value, JsonObject):
        value.set_type_recursively()
      elif isinstance(value, list):
        for item in value:
          if isinstance(item, JsonObject):
            item.set_type_recursively()

  def __str__(self):
    return str(self.__dict__)

  @classmethod
  def make_from_dict(cls, input_dict):
    dict_without_id = input_dict
    _id = dict_without_id.pop("_id", None)
    obj = jsonpickle.decode(json_util.dumps(dict_without_id))
    obj._id = _id
    obj.set_type_recursively()
    logging.info(obj)
    return obj

  @classmethod
  def make_from_pickledstring(cls, pickle):
    obj = jsonpickle.decode(pickle)
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
      collection.find_one({"_id": ObjectId(id)}))

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
  def from_details(cls, title, authors, path, targets=[]):
    book_portion = BookPortion()
    book_portion.title = title
    book_portion.authors = authors
    book_portion.path = path
    book_portion.targets = targets
    return book_portion

  @classmethod
  def from_path(cls, collection, path):
    book_portion = BookPortion()
    book_portion.set_from_dict(collection.find_one({"path": path}))
    return book_portion


class AnnotationSource(JsonObject):
  @classmethod
  def from_details(cls, type, id):
    source = AnnotationSource()
    source.type = type
    source.id = id
    return source


class Annotation(JsonObject):
  def set_base_details(self, targets, source):
    self.targets = targets
    self.source = source


class ImageTarget(Target):
  @classmethod
  def from_details(cls, container_id, x1=-1, y1=-1, x2=-1, y2=-1):
    target = ImageTarget()
    target.container_id = container_id
    target.x1 = x1
    target.y1 = y1
    target.x2 = x2
    target.y2 = y2
    return target


# Targets: ImageTarget for a BookPortion
class ImageAnnotation(Annotation):
  @classmethod
  def from_details(cls, targets, source):
    annotation = ImageAnnotation()
    annotation.set_base_details(targets, source)
    return annotation


class TextContent(JsonObject):
  @classmethod
  def from_details(cls, text, language="UNK", encoding="UNK"):
    text_content = TextContent()
    text_content.text = text
    text_content.language = language
    text_content.encoding = encoding
    return text_content


# Targets: ImageAnnotation(s)
class TextAnnotation(Annotation):
  @classmethod
  def from_details(cls, targets, source, content):
    annotation = TextAnnotation()
    annotation.set_base_details(targets, source)
    annotation.content = content
    return annotation


class TinantaDetails(JsonObject):
  @classmethod
  def from_details(cls, targets, source, lakAra, puruSha, vachana):
    annotation = TinantaDetails()
    annotation.set_base_details(targets, source)
    annotation.lakAra = lakAra
    annotation.puruSha = puruSha
    annotation.vachana = vachana
    return annotation


class SubantaDetails(JsonObject):
  @classmethod
  def from_details(cls, targets, source, linga, vibhakti, vachana):
    annotation = SubantaDetails()
    annotation.set_base_details(targets, source)
    annotation.linga = linga
    annotation.vibhakti = vibhakti
    annotation.vachana = vachana
    return annotation


class TextTarget(Target):
  @classmethod
  def from_details(cls, container_id, start_offset=-1, end_offset=-1):
    target = TextTarget()
    target.container_id = container_id
    target.start_offset = start_offset
    target.end_offset = end_offset
    return target


# Targets: TextTarget pointing to TextAnnotation
class PadaAnnotation(Annotation):
  @classmethod
  def from_details(cls, targets, source, word, root, tinanta_details, subanta_details):
    annotation = PadaAnnotation()
    annotation.set_base_details(targets, source)
    annotation.word = word
    annotation.root = root
    annotation.tinanta_details = tinanta_details
    annotation.subanta_details = subanta_details
    return annotation


# Targets: two PadaAnnotations
class SandhiAnnotation(Annotation):
  @classmethod
  def from_details(cls, targets, source, combined_string, type = "UNK"):
    annotation = SandhiAnnotation()
    annotation.set_base_details(targets, source)
    annotation.combined_string = combined_string
    annotation.type = type
    return annotation


# Targets: two or more PadaAnnotations
class SamaasaAnnotation(Annotation):
  @classmethod
  def from_details(cls, targets, source, combined_string, type = "UNK"):
    annotation = SamaasaAnnotation()
    annotation.set_base_details(targets, source)
    annotation.combined_string = combined_string
    annotation.type = type
    return annotation


# Targets: PadaAnnotations
class PadavibhaagaAnnotation(Annotation):
  @classmethod
  def from_details(self, targets, source):
    annotation = PadavibhaagaAnnotation()
    annotation.set_base_details(targets, source)
    return annotation

