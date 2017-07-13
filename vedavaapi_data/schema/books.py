import logging

from vedavaapi_data.schema import common
from vedavaapi_data.schema.common import JsonObject, TextContent, Target, TYPE_FIELD


class BookPortion(JsonObject):
  schema = common.recursively_merge(JsonObject.schema, ({
    "type": "object",
    "description": "A BookPortion could represent a Book or a chapter or a verse or a half-verse or a sentence or any such unit.",
    "properties": {
      TYPE_FIELD: {
        "enum": __name__ + ".BookPortion"
      },
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
      "base_data": {
        "type": "string",
        "enum": ["image", "text"]
      },
      "portion_class": {
        "type": "string",
        "description": "book, part, chapter, verse, line etc.."
      },
      "curated_content": TextContent.schema,
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
  def from_details(cls, path, title, authors=None, targets=None, base_data = None,
                   curated_content=None, portion_class=None):
    if authors is None:
      authors = []
    book_portion = BookPortion()
    book_portion.title = title
    book_portion.authors = authors
    # logging.debug(str(book_portion))
    book_portion.path = path

    targets = targets or []
    logging.debug(str(book_portion))
    book_portion.targets = targets
    if curated_content != None:
      book_portion.curated_content = curated_content
    if base_data != None:
      book_portion.base_data = base_data
    if portion_class != None:
      book_portion.portion_class = portion_class
    book_portion.validate_schema()
    return book_portion

  @classmethod
  def from_path(cls, path, db_interface):
    book_portion = JsonObject.find_one(filter={"path": path}, db_interface=db_interface)
    return book_portion