# -*- coding: utf-8 -*-
import logging
import unittest

import jsonpickle
from bson import ObjectId

import data_containers
from indicdocs import IndicDocs

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class TestDBRoundTrip(unittest.TestCase):
  test_db = IndicDocs("test_db")

  def test_BookPortion(self):
    book_portion = data_containers.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha", targets=[data_containers.Target.from_details(container_id="xyz")])

    json = jsonpickle.encode(book_portion)
    logging.info("json pickle is " + json)

    book_portions = self.test_db.db.book_portions
    logging.debug(book_portion.toJsonMap())
    result = book_portions.update({"path" : book_portion.path}, book_portion.toJsonMap(), upsert=True)
    logging.debug("update result is "  + str(result))

    book_portion_retrieved = data_containers.BookPortion.from_path(collection=book_portions, path="myrepo/halAyudha")
    logging.info(str(book_portion_retrieved.toJsonMap()))
    logging.info(str(book_portion.toJsonMap()))
    self.assertTrue(book_portion.equals_ignore_id(book_portion_retrieved))

  def test_ImageAnnotation(self):
    target_page_id = ObjectId()
    annotation = data_containers.ImageAnnotation.from_details(targets=[
      data_containers.ImageAnnotation.ImageTarget.from_details(container_id=target_page_id)],
    source=data_containers.Annotation.Source.from_details("someProgram", "xyz.py"))

    annotations = self.test_db.db.annotations
    logging.debug(annotation.toJsonMap())

    result = annotations.update(annotation.toJsonMap(), annotation.toJsonMap(), upsert=True)
    logging.debug("update result is "  + str(result))

    annotation_retrieved = data_containers.JsonObject.make_from_dict(annotations.find_one(annotation.toJsonMap()))

    logging.info(str(annotation_retrieved.toJsonMap()))
    self.assertTrue(annotation.equals_ignore_id(annotation_retrieved))

  def test_TextAnnotation(self):
    target_image_id = ObjectId()
    annotation = data_containers.TextAnnotation.from_details(targets=[
      data_containers.Target.from_details(container_id=target_image_id)],
      source=data_containers.Annotation.Source.from_details("someOCRProgram", "xyz.py"), content=data_containers.TextContent.from_details(u"इदं नभसि म्भीषण"))

    annotations = self.test_db.db.annotations
    logging.debug(annotation.toJsonMap())

    result = annotations.update(annotation.toJsonMap(), annotation.toJsonMap(), upsert=True)
    logging.debug("update result is "  + str(result))

    annotation_retrieved = data_containers.JsonObject.make_from_dict(annotations.find_one(annotation.toJsonMap()))
    logging.info("annotation_retrieved has text " + annotation_retrieved.content.text)

    logging.info(str(annotation_retrieved.toJsonMap()))
    self.assertTrue(annotation.equals_ignore_id(annotation_retrieved))


if __name__ == '__main__':
  unittest.main()