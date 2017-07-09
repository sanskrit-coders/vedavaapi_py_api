# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import logging
import os
import unittest

import jsonpickle
from bson import ObjectId

import textract
import vedavaapi_data.schema.books
from common.db import mongodb
from textract.backend import db
from vedavaapi_data.schema import ullekhanam, common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)
user_paths = os.environ['PYTHONPATH'].split(os.pathsep)

class TestDBRoundTrip(unittest.TestCase):
  db.initdb(dbname="test_db",
            client=mongodb.get_mongo_client("mongodb://vedavaapiUser:vedavaapiAdmin@localhost/"))
  test_db = textract.backend.db.textract_db

  def test_PickleDepickle(self):
    book_portion = vedavaapi_data.schema.books.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha",
      targets=[common.Target.from_details(container_id="xyz")])
    json_str = jsonpickle.encode(book_portion)
    logging.info("json_str pickle is " + json_str)
    obj = common.JsonObject.make_from_pickledstring(json_str)
    logging.info(obj.__class__)
    logging.info(obj)

    jsonMap = {u'py/object': u'data_containers.BookPortion', u'title': u'halAyudhakoshaH', u'path': u'myrepo/halAyudha',
               u'targets': [{u'py/object': u'data_containers.Target', u'container_id': u'xyz'}]}
    json_str = json.dumps(jsonMap)
    logging.info("json_str pickle is " + json_str)
    obj = common.JsonObject.make_from_pickledstring(json_str)
    logging.info(obj.__class__)
    logging.info(obj)

  # We deliberately don't use find_one_and_update below - as a test.
  def test_BookPortion(self):
    book_portion = vedavaapi_data.schema.books.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha",
      targets=[common.Target.from_details(container_id="xyz")])

    book_portions = self.test_db.books
    logging.debug(book_portion.to_json_map())
    book_portion.validate_schema()

    result = book_portions.update_doc(book_portion)
    logging.debug("update result is " + str(result))

    book_portion_retrieved = vedavaapi_data.schema.books.BookPortion.from_path(path="myrepo/halAyudha", db_interface=book_portions)
    logging.info(book_portion_retrieved.__class__)
    logging.info(str(book_portion_retrieved.to_json_map()))
    logging.info(book_portion.to_json_map())
    self.assertTrue(book_portion.equals_ignore_id(book_portion_retrieved))

  def test_ImageAnnotation(self):
    target_page_id = ObjectId()
    annotation = ullekhanam.ImageAnnotation.from_details(targets=[
      ullekhanam.ImageTarget.from_details(container_id=str(target_page_id),
                                          rectangle=ullekhanam.Rectangle.from_details())],
      source=ullekhanam.AnnotationSource.from_details("someProgram", "xyz.py"))

    annotations = self.test_db.annotations
    logging.debug(annotation.to_json_map())

    result = annotations.update_doc(annotation)
    logging.debug("update result is " + str(result))

    annotation_retrieved = common.JsonObject.make_from_dict(annotations.find(annotation.to_json_map())[0])
    logging.info(annotation_retrieved.__class__)

    logging.info(str(annotation_retrieved.to_json_map()))
    self.assertTrue(annotation.equals_ignore_id(annotation_retrieved))

  def test_TextAnnotation(self):
    target_image_id = ObjectId()
    text_annotation_original = ullekhanam.TextAnnotation.from_details(targets=[
      common.Target.from_details(container_id=str(target_image_id))],
      source=ullekhanam.AnnotationSource.from_details("someOCRProgram", "xyz.py"),
      content=common.TextContent.from_details(u"इदं नभसि म्भीषण"))

    annotations = self.test_db.annotations
    logging.debug(text_annotation_original.to_json_map())
    logging.debug(annotations.__class__)
    text_annotation = text_annotation_original.update_collection(annotations)
    logging.info("annotation_retrieved has text " + text_annotation.content.text)

    logging.info(str(text_annotation.to_json_map()))
    self.assertTrue(text_annotation_original.equals_ignore_id(text_annotation))

  def test_FullSentence(self):
    # Add text annotation
    target_image_id = ObjectId()
    text_annotation = ullekhanam.TextAnnotation.from_details(targets=[
      common.Target.from_details(container_id=str(target_image_id))],
      source=ullekhanam.AnnotationSource.from_details("someOCRProgram", "xyz.py"),
      content=common.TextContent.from_details(u"रामो विग्रवान् धर्मः।"))
    logging.debug(text_annotation.to_json_map())

    annotations = self.test_db.annotations

    text_annotation = text_annotation.update_collection(annotations)
    logging.debug(text_annotation.to_json_map())

    samsAdhanI_source = ullekhanam.AnnotationSource.from_details("samsAdhanI", "xyz.py")

    # Add pada annotations
    pada_annotation_rAmaH = ullekhanam.PadaAnnotation.from_details(targets=[
      ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"रामः", root=u"राम",
      subanta_details=ullekhanam.SubantaDetails.from_details(linga=u"पुम्", vibhakti=1, vachana=1))
    pada_annotation_rAmaH = pada_annotation_rAmaH.update_collection(annotations)
    logging.debug(pada_annotation_rAmaH.to_json_map())

    pada_annotation_vigrahavAn = ullekhanam.PadaAnnotation.from_details(targets=[
      ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"विग्रहवान्", root=u"विग्रहवत्",
      subanta_details=ullekhanam.SubantaDetails.from_details(linga=u"पुम्", vibhakti=1, vachana=1))
    pada_annotation_vigrahavAn = pada_annotation_vigrahavAn.update_collection(annotations)
    logging.debug(pada_annotation_vigrahavAn.to_json_map())

    pada_annotation_avigrahavAn = ullekhanam.PadaAnnotation.from_details(targets=[
      ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"अविग्रहवान्", root=u"अविग्रहवत्",
      subanta_details=ullekhanam.SubantaDetails.from_details(linga=u"पुम्", vibhakti=1, vachana=1))
    pada_annotation_avigrahavAn = pada_annotation_avigrahavAn.update_collection(annotations)
    logging.debug(pada_annotation_avigrahavAn.to_json_map())

    pada_annotation_dharmaH = ullekhanam.PadaAnnotation.from_details(targets=[
      ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"धर्मः", root=u"धर्म",
      subanta_details=ullekhanam.SubantaDetails.from_details(linga=u"पुम्", vibhakti=1, vachana=1))
    pada_annotation_dharmaH = pada_annotation_dharmaH.update_collection(annotations)
    logging.debug(pada_annotation_dharmaH.to_json_map())

    pada_annotation_na = ullekhanam.PadaAnnotation.from_details(targets=[
      ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"न", root=u"न",
      subanta_details=ullekhanam.SubantaDetails.from_details(linga=u"पुम्", vibhakti=1, vachana=1))
    pada_annotation_na = pada_annotation_na.update_collection(annotations)
    logging.debug(pada_annotation_na.to_json_map())

    sandhi_annotation_rAmovigrahavAn = ullekhanam.SandhiAnnotation.from_details(targets=
    ullekhanam.TextTarget.from_containers(
      containers=[
        pada_annotation_rAmaH,
        pada_annotation_vigrahavAn]),
      source=samsAdhanI_source,
      combined_string=u"रामो विग्रहवान्")
    sandhi_annotation_rAmovigrahavAn = sandhi_annotation_rAmovigrahavAn.update_collection(annotations)
    logging.debug(sandhi_annotation_rAmovigrahavAn.to_json_map())

    sandhi_annotation_rAmoavigrahavAn = ullekhanam.SandhiAnnotation.from_details(targets=
    ullekhanam.TextTarget.from_containers(
      containers=[
        pada_annotation_rAmaH,
        pada_annotation_avigrahavAn]),
      source=samsAdhanI_source,
      combined_string=u"रामो विग्रहवान्")
    logging.debug(sandhi_annotation_rAmoavigrahavAn.to_json_map())


if __name__ == '__main__':
  unittest.main()
