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

  def set_base_details(self, targets, source):
    self.targets = targets
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

  @classmethod
  def from_details(cls, targets, source):
    annotation = ImageAnnotation()
    annotation.set_base_details(targets, source)
    annotation.validate_schema()
    return annotation


# Targets: ImageAnnotation(s) or  TextAnnotation or BookPortion
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
    annotation.content = content
    annotation.validate_schema()
    return annotation

class OffsetAddress(JsonObject):
  schema = common.recursively_merge(JsonObject.schema, {
    "type": "object",
    "properties": {
      "start": {
        "type": "integer"
      },
      "end": {
        "type": "integer"
      }
    }})

  @classmethod
  def from_details(cls, start, end):
    obj = OffsetAddress()
    obj.start = start
    obj.end = end
    obj.validate_schema()
    return obj


class TextTarget(Target):
  schema = common.recursively_merge(Target.schema, ({
    "type": "object",
    "properties": {
      "shabda_id": {
        "type": "string",
        "description": "Format: pada_index.shabda_index or just pada_index."
                       "Suppose that some shabda in 'rāgādirogān satatānuṣaktān' is being targetted. "
                       "This has the following pada-vigraha: rāga [comp.]-ādi [comp.]-roga [ac.p.m.]  satata [comp.]-anuṣañj [ac.p.m.]."
                       "Then, rāga has the id 1.1. roga has id 1.3. satata has the id 2.1."
      },
      "offset_address": OffsetAddress.schema
    },
  }))

  @classmethod
  def from_details(cls, container_id, shabda_id=None, offset_address = None):
    target = TextTarget()
    target.container_id = container_id
    if shabda_id != None:
      target.shabda_id = shabda_id
    if offset_address != None:
      target.offset_address = offset_address
    target.validate_schema()
    return target


class PadaAnnotation(Annotation):
  schema = common.recursively_merge(Annotation.schema, ({
    "type": "object",
    "properties": {
      "targets": {
        "type": "array",
        "items": TextTarget.schema
      },
      "word": {
        "type": "string"
      },
      "root": {
        "type": "string"
      }
    },
  }))

  def set_base_details(self, targets, source, word, root):
    super(PadaAnnotation, self).set_base_details(targets, source)
    self.word = word
    self.root = root

  @classmethod
  def from_details(cls, targets, source, word, root):
    annotation = PadaAnnotation()
    annotation.set_base_details(targets, source, word, root)
    annotation.validate_schema()
    return annotation


# Targets: TextTarget pointing to TextAnnotation
class SubantaAnnotation(PadaAnnotation):
  schema = common.recursively_merge(PadaAnnotation.schema, ({
    "type": "object",
    "properties": {
      "linga": {
        "type": "string"
      },
      "vibhakti": {
        "type": "integer"
      },
      "vachana": {
        "type": "integer"
      }
    },
  }))

  @classmethod
  def from_details(cls, targets, source, word, root, linga, vibhakti, vachana):
    obj = SubantaAnnotation()
    obj.set_base_details(targets, source, word, root)
    obj.linga = linga
    obj.vibhakti = vibhakti
    obj.vachana = vachana
    obj.validate_schema()
    return obj


class TinantaAnnotation(PadaAnnotation):
  schema = common.recursively_merge(PadaAnnotation.schema, ({
    "type": "object",
    "properties": {
      "lakAra": {
        "type": "string"
      },
      "puruSha": {
        "type": "string"
      },
      "vachana": {
        "type": "integer"
      }
    },
  }))

  @classmethod
  def from_details(cls, targets, source, word, root, lakAra, puruSha, vachana):
    obj = TinantaAnnotation()
    obj.set_base_details(targets, source, word, root)
    obj.lakAra = lakAra
    obj.puruSha = puruSha
    obj.vachana = vachana
    obj.validate_schema()
    return obj


# Targets: two PadaAnnotations
class SandhiAnnotation(Annotation):
  schema = common.recursively_merge(Annotation.schema, ({
    "type": "object",
    "properties": {
      "combined_string": {
        "type": "string"
      },
      "type": {
        "type": "string"
      }
    },
    "required": ["combined_string"]
  }))

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
  schema = common.recursively_merge(Target.schema, ({
    "type": "object",
    "properties": {
      "combined_string": {
        "type": "string"
      },
      "type": {
        "type": "string"
      }
    },
    "required": ["combined_string"]
  }))

  @classmethod
  def from_details(cls, targets, source, combined_string, type="UNK"):
    annotation = SamaasaAnnotation()
    annotation.set_base_details(targets, source)
    annotation.combined_string = combined_string
    annotation.type = type
    annotation.validate_schema()
    return annotation
