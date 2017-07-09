import logging

from vedavaapi_data.schema import common
from vedavaapi_data.schema.common import JsonObject, TextContent, Target


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