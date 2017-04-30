import pymongo
import re
from bson.objectid import ObjectId
from pymongo.database import Database

from pymongo import MongoClient

import backend
from backend import data_containers
from backend.config import *
from docimage import *

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

  def insert(self, book):
    self.db_collection.update({"path": book["path"]}, book, upsert=True)
    return self.db_collection.find({'path': book["path"]}).count()

  def list(self, pattern=None):
    iter = self.db_collection.find({}, {'_id': False, 'pages': False})
    matches = [b for b in iter if not pattern or re.search(pattern, b['path'])]
    return matches

  def getPageByIdx(self, book, idx):
    return book.pages[idx]

  def getPageByName(self, book, pagename):
    page = book.find({"pages.fname", pagename})
    return page

  def get(self, path):
    book = self.db_collection.find_one({'path': path})
    if book is not None:
      book['_id'] = str(book['_id'])
    return book

  def importAll(self, rootdir, pattern=None):
    logging.info("Importing books into database from " + rootdir)
    cmd = "find " + rootdir + " \( \( -path '*/.??*' \) -prune \) , \( -path '*book.json' \) -follow -print; true"
    try:
      results = mycheck_output(cmd)
    except Exception as e:
      logging.error("Error in find: " + str(e))
      return 0

    nbooks = 0

    for f in results.split("\n"):
      if not f:
        continue
      bpath, fname = os.path.split(f.replace(rootdir + "/", ""))
      logging.info("    " + bpath)
      if pattern and not re.search(pattern, bpath, re.IGNORECASE):
        continue
      winfo = {}
      try:
        with open(f) as fhandle:
          book_data = json.load(fhandle)
          # logging.info(json.dumps(book_data, indent=4))
          book_data["path"] = bpath
          book = data_containers.BookPortion.from_path(self.db_collection, bpath)
          # TODO - Add a not below.
          if not hasattr(book, "_id"):
            logging.info("Importing afresh! %s " % json.dumps(book_data, indent=2))
            pages = []
            page_index = 0
            for page in book_data['pages']:
              page_obj = data_containers.BookPortion.from_details(
                title = "pg_%000d" % page_index, path=page['fname'])
              # logging.debug(str(page_obj))
              page_node = data_containers.JsonObjectNode.from_details(content=page_obj)
              logging.debug(str(page_node))
              pages.append(page_node)
              page_index = page_index + 1

            book_portion_node = data_containers.JsonObjectNode.from_details(content=book, children=pages)
            # logging.debug(str(book_portion_node))


            abspath = join(rootdir, bpath)
            book_mfile = join(abspath, "book_v2.json")
            logging.info("writing to " + book_mfile)
            try:
              with open(book_mfile, "w") as f:
                f.write(str(book_portion_node))
            except Exception as e:
              return logging.error("Error writing " + book_mfile + " : ".format(e))
            book_portion_node.update_collection(self.db_collection)
            logging.debug(str(book_portion_node))
            nbooks = nbooks + 1
      except Exception as e:
        logging.error("Skipped book_data " + str(f) + ". Error:" + str(e))
    return nbooks


# Encapsulates the annotations collection.
class Annotations(CollectionWrapper):
  def __init__(self, db_collection):
    logging.info("Initializing collection :" + str(db_collection))
    super(Annotations, self).__init__(db_collection)

  def get(self, anno_id):
    res = self.annotations.find_one({'_id': ObjectId(anno_id)})
    res['_id'] = str(res['_id'])
    return res

  def get_image(self, anno_id):
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
    imgpath = join(repodir(), join(anno_obj['bpath'], page['fname']))
    logging.info("Image path = " + imgpath)
    page_img = DocImage(imgpath)
    return page_img

  def insert(self, anno):
    id = self.annotations.insert(anno)
    return str(id)

  def update(self, anno_id, anno):
    # pprint(anno)
    result = self.annotations.update({'_id': ObjectId(anno_id)}, {"$set": anno})
    isSuccess = (result['n'] > 0)
    return isSuccess

  def segment(self, anno_id):
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
    [fname, ext] = os.path.splitext(page['fname']);
    imgpath = join(repodir(), join(anno_obj['bpath'], page['fname']))
    workingImgPath = join(repodir(), join(anno_obj['bpath'], fname + "_working.jpg"))
    logging.info("Image path = " + imgpath)
    logging.info("Working Image path = " + workingImgPath)
    page_img = DocImage(imgpath, workingImgPath)

    known_segments = DisjointSegments()
    # Give me all the non-overlapping user-touched segments in this page.
    for a in anno_obj['anno']:
      a = ImgSegment(a)
      if a.state == 'system_inferred':
        continue
      a['score'] = float(1.0)  # Set the max score for user-identified segments
      # Prevent image matcher from changing user-identified segments
      known_segments.insert(a)

    # Create segments taking into account known_segments
    matches = page_img.find_segments(0, 0, known_segments)
    # logging.info("Matches = " + json.dumps(matches))
    # logging.info("Segments = " + json.dumps(known_segments.segments))
    for r in matches:
      # and propagate its text to them
      r['state'] = 'system_inferred'

    self.update(anno_id, {'anno': known_segments.segments})
    return True

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
    imgpath = join(repodir(), join(anno_obj['bpath'], page['fname']))
    logging.info("Image path = " + imgpath)
    page_img = DocImage(imgpath)

    known_segments = DisjointSegments()
    srch_segments = []
    for a in anno_obj['anno']:
      a = ImgSegment(a)
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

    known_segments.segments.sort()
    # for r in known_segments.segments:
    #   logging.info(str(r))
    # print(known_segments.segments)
    # new_anno = sorted(DotDict(new_anno), key=attrgetter('x', 'y', 'w', 'h'))
    # Save the updated annotations
    self.update(anno_id, {'anno': known_segments.segments})
    return True


# Encapsulates the sections collection.
class Sections(CollectionWrapper):
  def __init__(self, db_collection):
    super(Sections, self).__init__(db_collection)

  def get(self, sec_id):
    res = self.sections.find_one({'_id': ObjectId(sec_id)})
    res['_id'] = str(res['_id'])
    return res

  def insert(self, sec):
    result = self.sections.insert_one(sec)
    return str(result.inserted_id)

  def update(self, sec_id, section):
    result = self.sections.update({'_id': ObjectId(sec_id)}, section)
    return result['n'] > 0


# Encapsulates the users collection.
class Users(CollectionWrapper):
  def __init__(self, db_collection):
    super(Users, self).__init__(db_collection)

  def get(self, user_id):
    res = self.users.find_one({'_id': ObjectId(user_id)})
    res['_id'] = str(res['_id'])
    return res

  def getBySocialId(self, social_id):
    res = self.users.find_one({'social_id': social_id})
    if res is not None: res['_id'] = str(res['_id'])
    return res

  def insert(self, user_data):
    result = self.users.insert_one(user_data)
    result = self.get(result.inserted_id)
    result['_id'] = str(result['_id'])
    return result

  def update(self, user_id, user_data):
    result = self.users.update({'_id': ObjectId(user_id)}, user_data)
    return result['n'] > 0


# class Users:
#    def __init__(docdb):
#        self.users = docdb['users']

