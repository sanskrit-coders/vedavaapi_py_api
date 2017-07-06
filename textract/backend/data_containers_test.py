# -*- coding: utf-8 -*-
import json
import logging
import unittest
import common

import jsonpickle
from bson import ObjectId

import common.data_containers
import data_containers
from mongodb import DBWrapper

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class TestDBRoundTrip(unittest.TestCase):
  test_db = DBWrapper(dbname="test_db", client=common.get_mongo_client())

  def test_PickleDepickle(self):
    book_portion = data_containers.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha",
      targets=[common.data_containers.Target.from_details(container_id="xyz")])
    json_str = jsonpickle.encode(book_portion)
    logging.info("json_str pickle is " + json_str)
    obj = common.data_containers.JsonObject.make_from_pickledstring(json_str)
    logging.info(obj.__class__)
    logging.info(obj)

    jsonMap = {u'py/object': u'data_containers.BookPortion', u'title': u'halAyudhakoshaH', u'path': u'myrepo/halAyudha',
               u'targets': [{u'py/object': u'data_containers.Target', u'container_id': u'xyz'}]}
    json_str = json.dumps(jsonMap)
    logging.info("json_str pickle is " + json_str)
    obj = common.data_containers.JsonObject.make_from_pickledstring(json_str)
    logging.info(obj.__class__)
    logging.info(obj)

  # We deliberately don't use find_one_and_update below - as a test.
  def test_BookPortion(self):
    book_portion = data_containers.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha",
      targets=[common.data_containers.Target.from_details(container_id="xyz")])

    book_portions = self.test_db.db.book_portions
    logging.debug(book_portion.to_json_map())
    book_portion.validate_schema()

    result = book_portions.update({"path": book_portion.path}, book_portion.to_json_map(), upsert=True)
    logging.debug("update result is " + str(result))

    book_portion_retrieved = common.data_containers.JsonObject.make_from_dict(
      book_portions.find_one({"path": "myrepo/halAyudha"}))
    logging.info(book_portion_retrieved.__class__)
    logging.info(str(book_portion_retrieved.to_json_map()))
    logging.info(book_portion.to_json_map())
    self.assertTrue(book_portion.equals_ignore_id(book_portion_retrieved))

  def test_ImageAnnotation(self):
    target_page_id = ObjectId()
    annotation = data_containers.ImageAnnotation.from_details(targets=[
      data_containers.ImageTarget.from_details(container_id=str(target_page_id), rectangle=data_containers.Rectangle.from_details())],
      source=data_containers.AnnotationSource.from_details("someProgram", "xyz.py"))

    annotations = self.test_db.db.annotations
    logging.debug(annotation.to_json_map())

    result = annotations.update(annotation.to_json_map(), annotation.to_json_map(), upsert=True)
    logging.debug("update result is " + str(result))

    annotation_retrieved = common.data_containers.JsonObject.make_from_dict(annotations.find_one(annotation.to_json_map()))
    logging.info(annotation_retrieved.__class__)

    logging.info(str(annotation_retrieved.to_json_map()))
    self.assertTrue(annotation.equals_ignore_id(annotation_retrieved))

  def test_TextAnnotation(self):
    target_image_id = ObjectId()
    text_annotation_original = data_containers.TextAnnotation.from_details(targets=[
      common.data_containers.Target.from_details(container_id=str(target_image_id))],
      source=data_containers.AnnotationSource.from_details("someOCRProgram", "xyz.py"),
      content=data_containers.TextContent.from_details(u"इदं नभसि म्भीषण"))

    annotations = self.test_db.db.annotations
    logging.debug(text_annotation_original.to_json_map())
    text_annotation = text_annotation_original.update_collection(annotations)
    logging.info("annotation_retrieved has text " + text_annotation.content.text)

    logging.info(str(text_annotation.to_json_map()))
    self.assertTrue(text_annotation_original.equals_ignore_id(text_annotation))

  def test_FullSentence(self):
    # Add text annotation
    target_image_id = ObjectId()
    text_annotation = data_containers.TextAnnotation.from_details(targets=[
      common.data_containers.Target.from_details(container_id=str(target_image_id))],
      source=data_containers.AnnotationSource.from_details("someOCRProgram", "xyz.py"),
      content=data_containers.TextContent.from_details(u"रामो विग्रवान् धर्मः।"))
    logging.debug(text_annotation.to_json_map())

    annotations = self.test_db.db.annotations

    text_annotation = text_annotation.update_collection(annotations)
    logging.debug(text_annotation.to_json_map())

    samsAdhanI_source = data_containers.AnnotationSource.from_details("samsAdhanI", "xyz.py")

    # Add pada annotations
    pada_annotation_rAmaH = data_containers.PadaAnnotation.from_details(targets=[
      data_containers.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"रामः", root=u"राम",
      subanta_details=data_containers.SubantaDetails.from_details(linga=u"पुम्", vibhakti=1, vachana=1))
    pada_annotation_rAmaH = pada_annotation_rAmaH.update_collection(annotations)
    logging.debug(pada_annotation_rAmaH.to_json_map())

    pada_annotation_vigrahavAn = data_containers.PadaAnnotation.from_details(targets=[
      data_containers.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"विग्रहवान्", root=u"विग्रहवत्",
      subanta_details=data_containers.SubantaDetails.from_details(linga=u"पुम्", vibhakti=1, vachana=1))
    pada_annotation_vigrahavAn = pada_annotation_vigrahavAn.update_collection(annotations)
    logging.debug(pada_annotation_vigrahavAn.to_json_map())

    pada_annotation_avigrahavAn = data_containers.PadaAnnotation.from_details(targets=[
      data_containers.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"अविग्रहवान्", root=u"अविग्रहवत्",
      subanta_details=data_containers.SubantaDetails.from_details(linga=u"पुम्", vibhakti=1, vachana=1))
    pada_annotation_avigrahavAn = pada_annotation_avigrahavAn.update_collection(annotations)
    logging.debug(pada_annotation_avigrahavAn.to_json_map())

    pada_annotation_dharmaH = data_containers.PadaAnnotation.from_details(targets=[
      data_containers.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"धर्मः", root=u"धर्म",
      subanta_details=data_containers.SubantaDetails.from_details(linga=u"पुम्", vibhakti=1, vachana=1))
    pada_annotation_dharmaH = pada_annotation_dharmaH.update_collection(annotations)
    logging.debug(pada_annotation_dharmaH.to_json_map())

    pada_annotation_na = data_containers.PadaAnnotation.from_details(targets=[
      data_containers.TextTarget.from_details(container_id=str(text_annotation._id))],
      source=samsAdhanI_source, word=u"न", root=u"न",
      subanta_details=data_containers.SubantaDetails.from_details(linga=u"पुम्", vibhakti=1, vachana=1))
    pada_annotation_na = pada_annotation_na.update_collection(annotations)
    logging.debug(pada_annotation_na.to_json_map())

    sandhi_annotation_rAmovigrahavAn = data_containers.SandhiAnnotation.from_details(targets=
                                                                                     data_containers.TextTarget.from_containers(
                                                                                       containers=[
                                                                                         pada_annotation_rAmaH,
                                                                                         pada_annotation_vigrahavAn]),
                                                                                     source=samsAdhanI_source,
                                                                                     combined_string=u"रामो विग्रहवान्")
    sandhi_annotation_rAmovigrahavAn = sandhi_annotation_rAmovigrahavAn.update_collection(annotations)
    logging.debug(sandhi_annotation_rAmovigrahavAn.to_json_map())

    sandhi_annotation_rAmoavigrahavAn = data_containers.SandhiAnnotation.from_details(targets=
                                                                                      data_containers.TextTarget.from_containers(
                                                                                        containers=[
                                                                                          pada_annotation_rAmaH,
                                                                                          pada_annotation_avigrahavAn]),
                                                                                      source=samsAdhanI_source,
                                                                                      combined_string=u"रामो विग्रहवान्")
    logging.debug(sandhi_annotation_rAmoavigrahavAn.to_json_map())


  def test_JsonObjectNode(self):
    self.test_db.importAll("~/vedavaapi_py_api/textract/example-repo")
    book = common.data_containers.JsonObject.find_one(some_collection=self.test_db.books.db_collection, filter={"path": "kannada/skt-dict"})
    logging.debug(str(book))
    json_node = common.data_containers.JsonObjectNode.from_details(content=book)
    json_node.fill_descendents(self.test_db.books.db_collection)
    logging.debug(str(json_node))
    self.assertEquals(json_node.children.__len__(), 11)



if __name__ == '__main__':
  unittest.main()
