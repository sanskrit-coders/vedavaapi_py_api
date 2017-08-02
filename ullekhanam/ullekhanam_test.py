# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import logging
import os
import unittest
from bson import ObjectId

import sanskrit_data.schema.books
from sanskrit_data.db import mongodb
from sanskrit_data.schema import ullekhanam, common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)
user_paths = os.environ['PYTHONPATH'].split(os.pathsep)

class TestDBRoundTrip(unittest.TestCase):
  import common
  common.set_configuration()
  server_config = common.server_config


  from ullekhanam.backend import db as backend_db
  from sanskrit_data.db import mongodb
  mongo_client = mongodb.Client(url=server_config["mongo_host"])
  ullekhanam_db = mongo_client.get_database(db_name = "test_db")
  backend_db.initdb(db=ullekhanam_db)
  test_db = backend_db.ullekhanam_db

  def test_PickleDepickle(self):
    book_portion = sanskrit_data.schema.books.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha",
      targets=[common.Target.from_details(container_id="xyz")])
    json_str = str(book_portion)
    logging.info("json_str pickle is " + json_str)
    obj = common.JsonObject.make_from_pickledstring(json_str)
    logging.info(obj.__class__)
    logging.info(obj)

    jsonMap = {u'jsonClass': u'BookPortion', u'title': u'halAyudhakoshaH', u'path': u'myrepo/halAyudha',
               u'targets': [{u'jsonClass': u'Target', u'container_id': u'xyz'}]}
    json_str = json.dumps(jsonMap)
    logging.info("json_str pickle is " + json_str)
    obj = common.JsonObject.make_from_pickledstring(json_str)
    logging.info(obj.__class__)
    logging.info(obj)

  # We deliberately don't use find_one_and_update below - as a test.
  def test_BookPortion(self):
    module = self.__module__

    book_portion = sanskrit_data.schema.books.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha",
      targets=[common.Target.from_details(container_id="xyz")])

    book_portions = self.test_db
    logging.debug(book_portion.to_json_map())
    book_portion.validate_schema()

    result = book_portions.update_doc(book_portion.to_json_map())
    logging.debug("update result is " + str(result))

    book_portion_retrieved = sanskrit_data.schema.books.BookPortion.from_path(path="myrepo/halAyudha", db_interface=book_portions)
    logging.info(book_portion_retrieved.__class__)
    logging.info(str(book_portion_retrieved.to_json_map()))
    logging.info(book_portion.to_json_map())
    self.assertTrue(book_portion.equals_ignore_id(book_portion_retrieved))

  def test_ImageAnnotation(self):
    target_page_id = ObjectId()
    annotation = ullekhanam.ImageAnnotation.from_details(targets=[
      ullekhanam.ImageTarget.from_details(container_id=str(target_page_id),
                                          rectangle=ullekhanam.Rectangle.from_details())],
      source=ullekhanam.AnnotationSource.from_details("system_inferred", "xyz.py"))

    db = self.test_db
    logging.debug(annotation.to_json_map())

    result = db.update_doc(annotation.to_json_map())
    logging.debug("update result is " + str(result))

    annotation_retrieved = common.JsonObject.from_id(id=result._id, db_interface=db)
    logging.info(annotation_retrieved.__class__)

    logging.info(str(annotation_retrieved.to_json_map()))
    self.assertTrue(annotation.equals_ignore_id(annotation_retrieved))

  def test_TextAnnotation(self):
    text_annotation_original = ullekhanam.TextAnnotation.from_details(targets=[],
                                                                      source=ullekhanam.AnnotationSource.from_details("system_inferred", "xyz.py"),
                                                                      content=common.TextContent.from_details(text=u"इदं नभसि म्भीषण"))

    db = self.test_db
    logging.debug(text_annotation_original.to_json_map())
    logging.debug(db.__class__)
    text_annotation = text_annotation_original.update_collection(db)
    logging.info("annotation_retrieved has text " + text_annotation.content.text)

    logging.info(str(text_annotation.to_json_map()))
    self.assertTrue(text_annotation_original.equals_ignore_id(text_annotation))

  def test_FullSentence(self):
    # Add text annotation
    db = self.test_db

    book_portion = sanskrit_data.schema.books.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha")
    book_portion = book_portion.update_collection(db)

    target_image_id = ObjectId()
    text_annotation = ullekhanam.TextAnnotation.from_details(targets=[
      common.Target.from_details(container_id=book_portion._id)],
      source=ullekhanam.AnnotationSource.from_details("system_inferred", "xyz.py"),
      content=common.TextContent.from_details(text=u"रामो विग्रवान् धर्मः।"))
    logging.debug(text_annotation.to_json_map())

    text_annotation = text_annotation.update_collection(db)
    logging.debug(text_annotation.to_json_map())

    samsAdhanI_source = ullekhanam.AnnotationSource.from_details("system_inferred", "samsAdhanI/xyz.py")

    # Add pada db
    pada_annotation_rAmaH = ullekhanam.SubantaAnnotation.from_details(targets=[
      ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"रामः", root=u"राम",
      linga=u"pum", vibhakti="1", vachana=1)
    pada_annotation_rAmaH = pada_annotation_rAmaH.update_collection(db)
    logging.debug(pada_annotation_rAmaH.to_json_map())

    pada_annotation_vigrahavAn = ullekhanam.SubantaAnnotation.from_details(targets=[
      ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"विग्रहवान्", root=u"विग्रहवत्",
      linga=u"pum", vibhakti="1", vachana=1)
    pada_annotation_vigrahavAn = pada_annotation_vigrahavAn.update_collection(db)
    logging.debug(pada_annotation_vigrahavAn.to_json_map())

    pada_annotation_avigrahavAn = ullekhanam.SubantaAnnotation.from_details(targets=[
      ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"अविग्रहवान्", root=u"अविग्रहवत्",
      linga=u"pum", vibhakti="1", vachana=1)
    pada_annotation_avigrahavAn = pada_annotation_avigrahavAn.update_collection(db)
    logging.debug(pada_annotation_avigrahavAn.to_json_map())

    pada_annotation_dharmaH = ullekhanam.SubantaAnnotation.from_details(targets=[
      ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"धर्मः", root=u"धर्म",
      linga=u"pum", vibhakti="1", vachana=1)
    pada_annotation_dharmaH = pada_annotation_dharmaH.update_collection(db)
    logging.debug(pada_annotation_dharmaH.to_json_map())

    pada_annotation_na = ullekhanam.SubantaAnnotation.from_details(targets=[
      ullekhanam.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"न", root=u"न",
      linga=u"pum", vibhakti="1", vachana=1)
    pada_annotation_na = pada_annotation_na.update_collection(db)
    logging.debug(pada_annotation_na.to_json_map())

    sandhi_annotation_rAmovigrahavAn = ullekhanam.SandhiAnnotation.from_details(targets=
    ullekhanam.TextTarget.from_containers(
      containers=[
        pada_annotation_rAmaH,
        pada_annotation_vigrahavAn]),
      source=samsAdhanI_source,
      combined_string=u"रामो विग्रहवान्")
    sandhi_annotation_rAmovigrahavAn = sandhi_annotation_rAmovigrahavAn.update_collection(db)
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
