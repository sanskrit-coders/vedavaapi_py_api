# -*- coding: utf-8 -*-
import logging

import jsonpickle

import common
from vedavaapi_data.schema.common import JsonObject, Target, TextContent

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

jsonpickle.set_encoder_options('simplejson', indent=2)


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

  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()
    assert common.check_class(self.type, [str, unicode])
    assert common.check_class(self.id, [str, unicode])

  @classmethod
  def from_details(cls, source_type, id):
    source = AnnotationSource()
    source.type = source_type
    source.id = id
    source.validate_schema()
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


  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()
    for target in self.targets:
      assert isinstance(target, Target), target.__class__
    assert isinstance(self.source, AnnotationSource), self.source.__class__

  def set_base_details(self, targets, source):
    self.targets = targets
    self.source = source
    self.validate_schema()


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


  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()

  @classmethod
  def from_details(cls, x=-1, y=-1, w=-1, h=-1, score=0.0):
    rectangle = Rectangle()
    rectangle.x1 = x
    rectangle.y1 = y
    rectangle.w = w
    rectangle.h = h
    rectangle.score = score
    rectangle.validate_schema()
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

  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()
    assert isinstance(self.rectangle, Rectangle), self.rectangle.__class__

  # TODO use w, h instead.
  @classmethod
  def from_details(cls, container_id, rectangle):
    target = ImageTarget()
    target.container_id = container_id
    target.rectangle = rectangle
    target.validate_schema()
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

  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()

  @classmethod
  def from_details(cls, targets, source):
    annotation = ImageAnnotation()
    annotation.set_base_details(targets, source)
    annotation.validate_schema()
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

  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()
    assert isinstance(self.content, TextContent), self.content.__class__

  @classmethod
  def from_details(cls, targets, source, content):
    annotation = TextAnnotation()
    annotation.set_base_details(targets, source)
    annotation.content = content
    annotation.validate_schema()
    return annotation


class TinantaDetails(JsonObject):

  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()
    assert common.check_class(self.lakAra, [str, unicode])
    assert common.check_class(self.puruSha, [str, unicode])
    assert common.check_class(self.vachana, [str, unicode])

  @classmethod
  def from_details(cls, lakAra, puruSha, vachana):
    obj = TinantaDetails()
    obj.lakAra = lakAra
    obj.puruSha = puruSha
    obj.vachana = vachana
    obj.validate_schema()
    return obj


class SubantaDetails(JsonObject):

  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()
    assert common.check_class(self.linga, [str, unicode])
    assert isinstance(self.vibhakti, int), self.vibhakti.__class__
    assert isinstance(self.vachana, int), self.vachana.__class__

  @classmethod
  def from_details(cls, linga, vibhakti, vachana):
    obj = SubantaDetails()
    obj.linga = linga
    obj.vibhakti = vibhakti
    obj.vachana = vachana
    obj.validate_schema()
    return obj


class TextTarget(Target):
  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()
    assert common.check_class(self.container_id, [str, unicode])
    assert isinstance(self.start_offset, int), self.start_offset.__class__
    assert isinstance(self.end_offset, int), self.end_offset.__class__

  @classmethod
  def from_details(cls, container_id, start_offset=-1, end_offset=-1):
    target = TextTarget()
    target.container_id = container_id
    target.start_offset = start_offset
    target.end_offset = end_offset
    target.validate_schema()
    return target


# Targets: TextTarget pointing to TextAnnotation
class PadaAnnotation(Annotation):
  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()
    assert common.check_class(self.word, [str, unicode])
    assert common.check_class(self.root, [str, unicode])
    assert isinstance(self.tinanta_details, TinantaDetails) or self.tinanta_details is None
    assert isinstance(self.subanta_details, SubantaDetails) or self.subanta_details is None

  @classmethod
  def from_details(cls, targets, source, word, root, tinanta_details=None, subanta_details=None):
    annotation = PadaAnnotation()
    common.check_list_item_types(targets, [TextTarget, Target])
    annotation.set_base_details(targets, source)
    annotation.word = word
    annotation.root = root
    annotation.tinanta_details = tinanta_details
    annotation.subanta_details = subanta_details
    annotation.validate_schema()
    return annotation


# Targets: two PadaAnnotations
class SandhiAnnotation(Annotation):
  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()
    assert common.check_class(self.combined_string, [str, unicode])
    assert common.check_class(self.type, [str, unicode])

  @classmethod
  def from_details(cls, targets, source, combined_string, type="UNK"):
    annotation = SandhiAnnotation()
    annotation.set_base_details(targets, source)
    annotation.combined_string = combined_string
    annotation.type = type
    annotation.validate_schema()
    return annotation


# Targets: two or more PadaAnnotations
class SamaasaAnnotation(Annotation):
  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()
    assert common.check_class(self.combined_string, [str, unicode])
    assert common.check_class(self.type, [str, unicode])

  @classmethod
  def from_details(cls, targets, source, combined_string, type="UNK"):
    annotation = SamaasaAnnotation()
    annotation.set_base_details(targets, source)
    annotation.combined_string = combined_string
    annotation.type = type
    annotation.validate_schema()
    return annotation


# Targets: PadaAnnotations
class PadavibhaagaAnnotation(Annotation):
  def validate_schema(self):
    super(AnnotationSource, self).validate_schema()

  @classmethod
  def from_details(self, targets, source):
    annotation = PadavibhaagaAnnotation()
    annotation.set_base_details(targets, source)
    return annotation
