import pymongo
import re
from bson.objectid import ObjectId

import common.data_containers
from common.config import *
from textract.docimage import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

logging.info("pymongo version is " + pymongo.__version__)


class CollectionWrapper(object):
  def __init__(self, db_collection):
    logging.info("Initializing collection :" + str(db_collection))
    self.db_collection = db_collection


# Encapsulates the book_portions collection.
class BookPortions(CollectionWrapper):
  def __init__(self, db_collection):
    logging.info("Initializing collection :" + str(db_collection))
    super(BookPortions, self).__init__(db_collection)

  def list_books(self, pattern=None):
    iter = common.data_containers.JsonObject.find(filter={"targets" : {"$exists" : False}}, some_collection=self.db_collection)
    matches = [b for b in iter if not pattern or re.search(pattern, b.path)]
    return matches

  def get(self, path):
    book = data_containers.BookPortion.from_path(path=path, collection=self.db_collection)
    book_node = common.data_containers.JsonObjectNode.from_details(content=book)
    book_node.fill_descendents(self.db_collection)
    return book_node


# Encapsulates the annotations collection.
class Annotations(CollectionWrapper):
  def __init__(self, db_collection):
    logging.info("Initializing collection :" + str(db_collection))
    super(Annotations, self).__init__(db_collection)

  def update_image_annotations(self, page):
    """return the page annotation with id = anno_id"""
    from os import path
    from textract.backend import paths
    page_image = DocImage.from_path(path=path.join(paths.DATADIR, page.path))
    known_annotations = page.get_targetting_entities(some_collection=self.db_collection,
                                                     entity_type=data_containers.ImageAnnotation.get_wire_typeid())
    if len(known_annotations):
      logging.warning("Annotations exist. Not detecting and merging.")
      return known_annotations
      # # TODO: fix the below and get segments.
      # #
      # # # Give me all the non-overlapping user-touched segments in this page.
      # for annotation in known_annotations:
      #   target = annotation.targets[0]
      #   if annotation.source.type == 'human':
      #     target['score'] = float(1.0)  # Set the max score for user-identified segments
      #   # Prevent image matcher from changing user-identified segments
      #   known_annotation_targets.insert(target)

    # Create segments taking into account known_segments
    detected_regions = page_image.find_text_regions()
    logging.info("Matches = " + str(detected_regions))

    new_annotations = []
    for region in detected_regions:
      region.score = None
      target = data_containers.ImageTarget.from_details(container_id=page._id, rectangle=region)
      annotation = data_containers.ImageAnnotation.from_details(
        targets=[target], source=data_containers.AnnotationSource.from_details(type='system_inferred', id="pyCV2"))
      annotation = annotation.update_collection(self.db_collection)
      new_annotations.append(annotation)
    return new_annotations

  def propagate(self, anno_id):
    # Get the annotations from anno_id
    anno_obj = self.get(anno_id)
    if not anno_obj:
      return False

    # Get the containing book
    books = self.indicdocs.books
    book = books.get(anno_obj['bpath'])
    if not book:
      return False

    page = book['pages'][anno_obj['pgidx']]
    from os.path import join
    from textract.backend import paths
    imgpath = join(paths.DATADIR, join(anno_obj['bpath'], page['fname']))
    logging.info("Image path = " + imgpath)
    page_img = DocImage(imgpath)

    known_segments = DisjointRectangles()
    srch_segments = []
    for a in anno_obj['anno']:
      a = data_containers.Rectangle(a)
      if a.state == 'system_inferred':
        known_segments.insert(a)
        continue
      a['score'] = float(1.0)  # Set the max score for user-identified segments
      # Prevent image matcher from changing user-identified segments
      known_segments.insert(a)
      srch_segments.append(a)

    cfg = serverconfig()
    thres = cfg['template_match']['threshold']

    logging.info("segments to propagate = " + json.dumps(srch_segments))
    # logging.info("Known segments = " + json.dumps(known_segments.segments))
    # For each user-supplied annotation,
    for a in srch_segments:
      # Search for similar image segments within page
      # make sure they are spatially disjoint
      matches = page_img.find_recurrence(a, thres, known_segments)
      # logging.info("Matches = " + json.dumps(matches))
      for r in matches:
        # and propagate its text to them
        r['state'] = 'system_inferred'
        r['text'] = a.text

    known_segments.img_targets.sort()
    # for r in known_segments.segments:
    #   logging.info(str(r))
    # print(known_segments.segments)
    # new_anno = sorted(DotDict(new_anno), key=attrgetter('x', 'y', 'w', 'h'))
    # Save the updated annotations
    self.update(anno_id, {'anno': known_segments.img_targets})
    return True


# Encapsulates the users collection.
class Users(CollectionWrapper):
  def __init__(self, db_collection):
    super(Users, self).__init__(db_collection)

  def get(self, user_id):
    res = self.db_collection.find_one({'_id': ObjectId(user_id)})
    res['_id'] = str(res['_id'])
    return res

  def getBySocialId(self, social_id):
    res = self.db_collection.find_one({'social_id': social_id})
    if res is not None: res['_id'] = str(res['_id'])
    return res

  def insert(self, user_data):
    result = self.db_collection.insert_one(user_data)
    result = self.get(result.inserted_id)
    result['_id'] = str(result['_id'])
    return result

  def update(self, user_id, user_data):
    result = self.db_collection.update({'_id': ObjectId(user_id)}, user_data)
    return result['n'] > 0
