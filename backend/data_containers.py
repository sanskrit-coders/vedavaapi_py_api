# -*- coding: utf-8 -*-
import logging
import os

from pymongo import ReturnDocument

import jsonpickle
import jsonschema
from bson import ObjectId, json_util

import common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

jsonpickle.set_encoder_options('simplejson', indent=2)

TYPE_FIELD = "py/object"

__location__ = os.path.realpath(
  os.path.join(os.getcwd(), os.path.dirname(__file__)))

class JsonObject(object):
  def __init__(self):
    self.set_type()

  @classmethod
  def make_from_dict(cls, input_dict):
    dict_without_id = input_dict
    _id = dict_without_id.pop("_id", None)
    obj = jsonpickle.decode(json_util.dumps(dict_without_id))
    obj._id = _id
    obj.set_type_recursively()
    # logging.debug(obj)
    return obj

  @classmethod
  def make_from_pickledstring(cls, pickle):
    obj = jsonpickle.decode(pickle)
    return obj

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
    return jsonpickle.encode(self)

  def set_from_dict(self, input_dict):
    if input_dict:
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

  def to_json_map_via_pickle(self):
    return json_util.loads(jsonpickle.encode(self))

  def to_json_map(self):
    jsonMap = {}
    for key, value in self.__dict__.iteritems():
      if isinstance(value, JsonObject):
        jsonMap[key] = value.to_json_map()
      elif isinstance(value, list):
        jsonMap[key] = [item.to_json_map() if isinstance(item, JsonObject) else item for item in value]
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
      elif common.check_class(input, [str, unicode]):
        return input.encode('utf-8')
      else:
        return input

    dict1 = to_unicode(self.to_json_map())
    dict1.pop("_id", None)
    # logging.debug(self.__dict__)
    # logging.debug(dict1)
    dict2 = to_unicode(other.to_json_map())
    dict2.pop("_id", None)
    # logging.debug(other.__dict__)
    # logging.debug(dict2)
    return dict1 == dict2

  def update_collection(self, some_collection):
    if hasattr(self, "schema"):
      self.validate_schema()
    updated_doc = some_collection.find_one_and_update(self.to_json_map(), {"$set": self.to_json_map()}, upsert=True,
                                                      return_document=ReturnDocument.AFTER)
    return JsonObject.make_from_dict(updated_doc)

  def validate_schema(self):
    json_map = self.to_json_map()
    json_map.pop("_id", None)
    jsonschema.validate(json_map, self.schema)



# Not intended to be written to the database as is. Portions are expected to be extracted and written.
class JsonObjectNode(JsonObject):
  @classmethod
  def from_details(cls, content, children=None):
    if children is None:
      children = []
    node = JsonObjectNode()
    assert isinstance(content, JsonObject)
    node.content = content
    logging.debug(common.check_list_item_types(children, [JsonObjectNode]))
    assert common.check_list_item_types(children, [JsonObjectNode])
    node.children = children
    return node

  def update_collection(self, some_collection):
    self.content = self.content.update_collection(some_collection)
    for child in self.children:
      child.content.targets = [Target.from_details(str(self.content._id))]
      child.update_collection(some_collection)


class Target(JsonObject):
  schema = {
    "type": "object",
    "properties": {
      "container_id": {
        "type": "string"
      }
    },
    "required": ["container_id"]
  }

  @classmethod
  def from_details(cls, container_id):
    target = Target()
    target.container_id = container_id
    return target

  @classmethod
  def from_ids(cls, container_ids):
    target = Target()
    return [Target.from_details(str(container_id)) for container_id in container_ids]

  @classmethod
  def from_containers(cls, containers):
    return Target.from_ids(container_ids=[container._id for container in containers])


class BookPortion(JsonObject):
  schema = {
    "type": "object",
    "properties": {
      "title": {
        "type": "string"
      },
      "path": {
        "type": "string"
      },
      "authors": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "targets": {
        "type": "array",
        "items": Target.schema
      }
    },
    "required": ["path"]
  }

  @classmethod
  def from_details(cls, path, title, authors=None, targets=None):
    if authors is None:
      authors = []
    book_portion = BookPortion()
    assert common.check_class(title, [str]), title
    book_portion.title = title
    assert common.check_list_item_types(authors, [str, unicode]), authors
    book_portion.authors = authors
    assert common.check_class(path, [str, unicode]), path
    # logging.debug(str(book_portion))
    book_portion.path = path

    targets = targets or []
    assert common.check_list_item_types(targets, [Target])
    logging.debug(str(book_portion))
    book_portion.targets = targets
    return book_portion

  @classmethod
  def from_path(cls, collection, path):
    book_portion = BookPortion()
    book_portion.set_from_dict(collection.find_one({"path": path}))
    if not hasattr(book_portion, "path"):
      logging.info("Did not find %s in the db" % path)
      book_portion.path = path
    return book_portion


class AnnotationSource(JsonObject):
  @classmethod
  def from_details(cls, type, id):
    source = AnnotationSource()
    assert isinstance(type, str)
    assert isinstance(id, str)
    source.type = type
    source.id = id
    return source


class Annotation(JsonObject):
  def set_base_details(self, targets, source):
    for target in targets:
      assert isinstance(target, Target)
    self.targets = targets
    assert isinstance(source, AnnotationSource)
    self.source = source


class ImageTarget(Target):
  # TODO use w, h instead.
  @classmethod
  def from_details(cls, container_id, x1=-1, y1=-1, x2=-1, y2=-1):
    target = ImageTarget()
    target.container_id = container_id
    assert isinstance(x1, int)
    assert isinstance(y1, int)
    assert isinstance(x2, int)
    assert isinstance(y2, int)
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
    assert common.check_class(text, [str, unicode])
    assert isinstance(language, str)
    assert isinstance(encoding, str)
    text_content.text = text
    text_content.language = language
    text_content.encoding = encoding
    return text_content


# Targets: ImageAnnotation(s) or  TextAnnotation
class TextAnnotation(Annotation):
  @classmethod
  def from_details(cls, targets, source, content):
    annotation = TextAnnotation()
    annotation.set_base_details(targets, source)
    assert isinstance(content, TextContent)
    annotation.content = content
    return annotation


class TinantaDetails(JsonObject):
  @classmethod
  def from_details(cls, lakAra, puruSha, vachana):
    obj = TinantaDetails()
    assert common.check_class(lakAra, [str, unicode])
    assert common.check_class(puruSha, [str, unicode])
    assert common.check_class(vachana, [str, unicode])
    obj.lakAra = lakAra
    obj.puruSha = puruSha
    obj.vachana = vachana
    return obj


class SubantaDetails(JsonObject):
  @classmethod
  def from_details(cls, linga, vibhakti, vachana):
    obj = SubantaDetails()
    assert common.check_class(linga, [str, unicode])
    assert isinstance(vibhakti, int)
    assert isinstance(vachana, int)
    obj.linga = linga
    obj.vibhakti = vibhakti
    obj.vachana = vachana
    return obj


class TextTarget(Target):
  @classmethod
  def from_details(cls, container_id, start_offset=-1, end_offset=-1):
    target = TextTarget()
    assert isinstance(container_id, str)
    assert isinstance(start_offset, int)
    assert isinstance(end_offset, int)
    target.container_id = container_id
    target.start_offset = start_offset
    target.end_offset = end_offset
    return target


# Targets: TextTarget pointing to TextAnnotation
class PadaAnnotation(Annotation):
  @classmethod
  def from_details(cls, targets, source, word, root, tinanta_details=None, subanta_details=None):
    annotation = PadaAnnotation()
    common.check_list_item_types(targets, [TextTarget, Target])
    annotation.set_base_details(targets, source)
    assert common.check_class(word, [str, unicode])
    assert common.check_class(root, [str, unicode])
    assert isinstance(tinanta_details, TinantaDetails) or tinanta_details is None
    assert isinstance(subanta_details, SubantaDetails) or subanta_details is None
    annotation.word = word
    annotation.root = root
    annotation.tinanta_details = tinanta_details
    annotation.subanta_details = subanta_details
    return annotation


# Targets: two PadaAnnotations
class SandhiAnnotation(Annotation):
  @classmethod
  def from_details(cls, targets, source, combined_string, type="UNK"):
    annotation = SandhiAnnotation()
    annotation.set_base_details(targets, source)
    assert common.check_class(combined_string, [str, unicode])
    assert common.check_class(type, [str, unicode])
    annotation.combined_string = combined_string
    annotation.type = type
    return annotation


# Targets: two or more PadaAnnotations
class SamaasaAnnotation(Annotation):
  @classmethod
  def from_details(cls, targets, source, combined_string, type="UNK"):
    annotation = SamaasaAnnotation()
    annotation.set_base_details(targets, source)
    assert common.check_class(combined_string, [str, unicode])
    assert common.check_class(type, [str, unicode])
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
