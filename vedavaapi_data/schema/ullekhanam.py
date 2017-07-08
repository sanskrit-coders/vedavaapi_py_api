# -*- coding: utf-8 -*-
import logging

import jsonpickle

import common
from vedavaapi_data.schema.common import JsonObject, Target, TextContent, TYPE_FIELD

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

jsonpickle.set_encoder_options('simplejson', indent=2)


class BookPortion(JsonObject):
  schema = common.recursively_merge(JsonObject.schema, ({
    "type": "object",
    "description": "A BookPortion could represent a Book or a chapter or a verse or a half-verse or a sentence or any such unit.",
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
      "curatedContent": TextContent.schema,
      "targets": {
        "type": "array",
        "items": Target.schema,
        "description": "Id of the BookPortion of which this BookPortion is a part. It is an array only for consistency. "
                       "For any given BookPortion, one can get the right order of contained BookPortions by seeking all "
                       "BookPortions referring to it in the targets list, and sorting them by their path values."
      }
    },
    "required": ["path"]
  }))

  @classmethod
  def from_details(cls, path, title, authors=None, targets=None, text=None):
    if authors is None:
      authors = []
    book_portion = BookPortion()
    assert common.check_class(title, [str, unicode]), title
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
  def from_path(cls, path, db_interface):
    book_portion = JsonObject.find_one(filter={"path": path}, db_interface=db_interface)
    return book_portion


class AnnotationSource(JsonObject):
  schema = common.recursively_merge(JsonObject.schema, ({
    "type": "object",
    "properties": {
      "type": {
        "type": "string"
      },
      "id": {
        "type": "string"
      }
    },
    "required": ["type"]
  }))

  @classmethod
  def from_details(cls, source_type, id):
    source = AnnotationSource()
    assert common.check_class(source_type, [str, unicode])
    assert common.check_class(id, [str, unicode])
    source.type = source_type
    source.id = id
    return source


class Annotation(JsonObject):
  schema = common.recursively_merge(JsonObject.schema, ({
    "type": "object",
    "properties": {
      "source": AnnotationSource.schema,
      "targets": {
        "type": "array",
        "items": Target.schema
      }
    },
    "required": ["targets", "source"]
  }))

  def set_base_details(self, targets, source):
    for target in targets:
      assert isinstance(target, Target), target.__class__
    self.targets = targets
    assert isinstance(source, AnnotationSource), source.__class__
    self.source = source


class Rectangle(JsonObject):
  schema = common.recursively_merge(JsonObject.schema, ({
    "type": "object",
    "properties": {
      "x1": {
        "type": "integer"
      },
      "y1": {
        "type": "integer"
      },
      "w": {
        "type": "integer"
      },
      "h": {
        "type": "integer"
      },
    },
    "required": ["x1", "y1", "w", "h"]
  }))

  @classmethod
  def from_details(cls, x=-1, y=-1, w=-1, h=-1, score=0.0):
    rectangle = Rectangle()
    assert isinstance(x, int), x.__class__
    assert isinstance(y, int), y.__class__
    assert isinstance(w, int), w.__class__
    assert isinstance(h, int), h.__class__
    rectangle.x1 = x
    rectangle.y1 = y
    rectangle.w = w
    rectangle.h = h
    rectangle.score = score
    return rectangle

    # Two (segments are 'equal' if they overlap
    def __eq__(self, other):
      xmax = max(self.x, other.x)
      ymax = max(self.y, other.y)
      w = min(self.x+self.w, other.x+other.w) - xmax
      h = min(self.y+self.h, other.y+other.h) - ymax
      return w > 0 and h > 0

    def __ne__(self, other):
      return not self.__eq__(other)

    def __cmp__(self, other):
      if self == other:
        logging.info(str(self) + " overlaps " + str(other))
        return 0
      elif (self.y < other.y) or ((self.y == other.y) and (self.x < other.x)):
        return -1
      else:
        return 1


class ImageTarget(Target):
  schema = common.recursively_merge(Target.schema, ({
    "type": "object",
    "properties": {
      "rectangle": Rectangle.schema
    },
    "required": ["rectangle"]
  }))

  # TODO use w, h instead.
  @classmethod
  def from_details(cls, container_id, rectangle):
    target = ImageTarget()
    target.container_id = container_id
    assert isinstance(rectangle, Rectangle), rectangle.__class__
    target.rectangle = rectangle
    return target


# Targets: ImageTarget for a BookPortion
class ImageAnnotation(Annotation):
  schema = common.recursively_merge(Annotation.schema, ({
    "type": "object",
    "properties": {
      "targets": {
        "type": "array",
        "items": ImageTarget.schema
      }
    },
  }))

  @classmethod
  def from_details(cls, targets, source):
    annotation = ImageAnnotation()
    annotation.set_base_details(targets, source)
    return annotation


# Targets: ImageAnnotation(s) or  TextAnnotation
class TextAnnotation(Annotation):
  schema = common.recursively_merge(Annotation.schema, ({
    "type": "object",
    "properties": {
      "content": TextContent.schema,
    },
    "required": ["content"]
  }))

  @classmethod
  def from_details(cls, targets, source, content):
    annotation = TextAnnotation()
    annotation.set_base_details(targets, source)
    assert isinstance(content, TextContent), content.__class__
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
    assert isinstance(vibhakti, int), vibhakti.__class__
    assert isinstance(vachana, int), vachana.__class__
    obj.linga = linga
    obj.vibhakti = vibhakti
    obj.vachana = vachana
    return obj


class TextTarget(Target):
  @classmethod
  def from_details(cls, container_id, start_offset=-1, end_offset=-1):
    target = TextTarget()
    assert common.check_class(container_id, [str, unicode])
    assert isinstance(start_offset, int), start_offset.__class__
    assert isinstance(end_offset, int), end_offset.__class__
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