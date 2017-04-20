# -*- coding: utf-8 -*-
import json
import logging
import unittest

import jsonpickle
from bson import ObjectId
from pymongo import ReturnDocument

import data_containers
from indicdocs import IndicDocs

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class TestDBRoundTrip(unittest.TestCase):
  test_db = IndicDocs("test_db")

  def test_PickleDepickle(self):
    book_portion = data_containers.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha", targets=[data_containers.Target.from_details(container_id="xyz")])
    json_str = jsonpickle.encode(book_portion)
    logging.info("json_str pickle is " + json_str)
    obj = data_containers.JsonObject.make_from_pickledstring(json_str)
    logging.info(obj.__class__)
    logging.info(obj)

    jsonMap = {u'py/object': u'data_containers.BookPortion', u'title': u'halAyudhakoshaH', u'path': u'myrepo/halAyudha', u'targets': [{u'py/object': u'data_containers.Target', u'container_id': u'xyz'}]}
    json_str = json.dumps(jsonMap)
    logging.info("json_str pickle is " + json_str)
    obj = data_containers.JsonObject.make_from_pickledstring(json_str)
    logging.info(obj.__class__)
    logging.info(obj)

  def test_BookPortion(self):
    book_portion = data_containers.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha", targets=[data_containers.Target.from_details(container_id="xyz")])

    book_portions = self.test_db.db.book_portions
    logging.debug(book_portion.toJsonMap())
    result = book_portions.update({"path" : book_portion.path}, book_portion.toJsonMap(), upsert=True)
    logging.debug("update result is "  + str(result))

    book_portion_retrieved = data_containers.JsonObject.make_from_dict(book_portions.find_one({"path" : "myrepo/halAyudha"}))
    logging.info(book_portion_retrieved.__class__)
    logging.info(str(book_portion_retrieved.toJsonMap()))
    logging.info(book_portion.toJsonMap())
    self.assertTrue(book_portion.equals_ignore_id(book_portion_retrieved))

  def test_ImageAnnotation(self):
    target_page_id = ObjectId()
    annotation = data_containers.ImageAnnotation.from_details(targets=[
      data_containers.ImageTarget.from_details(container_id=str(target_page_id))],
    source=data_containers.AnnotationSource.from_details("someProgram", "xyz.py"))

    annotations = self.test_db.db.annotations
    logging.debug(annotation.toJsonMap())

    result = annotations.update(annotation.toJsonMap(), annotation.toJsonMap(), upsert=True)
    logging.debug("update result is "  + str(result))

    annotation_retrieved = data_containers.JsonObject.make_from_dict(annotations.find_one(annotation.toJsonMap()))
    logging.info(annotation_retrieved.__class__)

    logging.info(str(annotation_retrieved.toJsonMap()))
    self.assertTrue(annotation.equals_ignore_id(annotation_retrieved))

  def test_TextAnnotation(self):
    target_image_id = ObjectId()
    annotation = data_containers.TextAnnotation.from_details(targets=[
      data_containers.Target.from_details(container_id=str(target_image_id))],
      source=data_containers.AnnotationSource.from_details("someOCRProgram", "xyz.py"), content=data_containers.TextContent.from_details(u"इदं नभसि म्भीषण"))

    annotations = self.test_db.db.annotations
    logging.debug(annotation.toJsonMap())

    result = annotations.update(annotation.toJsonMap(), annotation.toJsonMap(), upsert=True)
    logging.debug("update result is "  + str(result))

    annotation_retrieved = data_containers.JsonObject.make_from_dict(annotations.find_one(annotation.toJsonMap()))
    logging.info("annotation_retrieved has text " + annotation_retrieved.content.text)

    logging.info(str(annotation_retrieved.toJsonMap()))
    self.assertTrue(annotation.equals_ignore_id(annotation_retrieved))


  def test_FullSentence(self):
    # Add text annotation
    target_image_id = ObjectId()
    text_annotation = data_containers.TextAnnotation.from_details(targets=[
      data_containers.Target.from_details(container_id=str(target_image_id))],
      source=data_containers.AnnotationSource.from_details("someOCRProgram", "xyz.py"), content=data_containers.TextContent.from_details(u"रामो विग्रवान् धर्मः।"))
    logging.debug(text_annotation.toJsonMap())

    annotations = self.test_db.db.annotations

    updated_doc = annotations.find_one_and_update(text_annotation.toJsonMap(),  { "$set": text_annotation.toJsonMap()}, upsert = True, return_document=ReturnDocument.AFTER)
    logging.debug(updated_doc)
    text_annotation = data_containers.JsonObject.make_from_dict(updated_doc)
    logging.debug(text_annotation.toJsonMap())

    samsAdhanI_source = data_containers.AnnotationSource.from_details("samsAdhanI", "xyz.py")

    # Add pada annotations
    pada_annotation_rAmaH = data_containers.PadaAnnotation.from_details(targets=[
      data_containers.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word="रामः", root="राम", subanta_details=data_containers.SubantaDetails.from_details(linga = "पुम्", vibhakti = 1, vachana = 1))
    json_str = jsonpickle.encode(pada_annotation_rAmaH)
    logging.info("json_str pickle is " + json_str)
    logging.debug(pada_annotation_rAmaH.toJsonMap())
    logging.debug(pada_annotation_rAmaH.toJsonMapViaPickle())
    updated_doc = annotations.find_one_and_update(pada_annotation_rAmaH.toJsonMap(),  { "$set": pada_annotation_rAmaH.toJsonMap()}, upsert = True, return_document=ReturnDocument.AFTER)
    logging.debug(updated_doc)
    pada_annotation_rAmaH = data_containers.JsonObject.make_from_dict(updated_doc)
    logging.debug(pada_annotation_rAmaH.toJsonMap())



if __name__ == '__main__':
  unittest.main()