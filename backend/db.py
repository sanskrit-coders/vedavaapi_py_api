import sys
from os.path import join

import cv2
from pymongo.database import Database

import logging
from pymongo import MongoClient

from backend.collections import BookPortions, Annotations, Sections, Users
from backend.config import setworkdir, workdir, initworkdir, setwlocaldir, DATADIR_BOOKS, INDICDOC_DBNAME, repodir
from docimage import DocImage

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

__indicdocs_db = None

# Encapsulates the main database.
class DBWrapper:
  def __init__(self, dbname):
    self.dbname = dbname
    self.initialize()

  #        if not database.write_concern.acknowledged:
  #            raise ConfigurationError('database must use '
  #                                     'acknowledged write_concern')

  def initialize(self):
    try:
      self.client = MongoClient()
      self.db = self.client[self.dbname]
      if not isinstance(self.db, Database):
        raise TypeError("database must be an instance of Database")
      self.books = BookPortions(self.db['book_portions'])
      self.annotations = Annotations(self.db['annotations'])
      self.sections = Sections(self.db['sections'])
      self.users = Users(self.db['users'])
    except Exception as e:
      print("Error initializing MongoDB database; aborting.", e)
      sys.exit(1)

  def reset(self):
    logging.info("Clearing IndicDocs database")
    self.client.drop_database(self.dbname)
    self.initialize()


def initdb(dbname, reset=False):
  global __indicdocs_db
  __indicdocs_db = DBWrapper(dbname)
  if reset:
    __indicdocs_db.reset()


def get_db():
  return __indicdocs_db


def main(args):
  setworkdir(workdir())
  initworkdir(False)
  setwlocaldir(DATADIR_BOOKS)
  initdb(INDICDOC_DBNAME, False)

  anno_id = args[0]
  get_db().annotations.propagate(anno_id)

  # Get the annotations from anno_id
  anno_obj = get_db().annotations.get(anno_id)
  if not anno_obj:
    return False

  # Get the containing book
  book = get_db().books.get(anno_obj['bpath'])
  if not book:
    return False

  page = book['pages'][anno_obj['pgidx']]
  imgpath = join(repodir(), join(anno_obj['bpath'], page['fname']))
  img = DocImage(imgpath)

  # logging.info(json.dumps(matches))
  rects = anno_obj['anno']
  seeds = [r for r in rects if r['state'] != 'system_inferred']
  img.annotate(rects)
  img.annotate(seeds, (0, 255, 0))
  cv2.namedWindow('Annotated image', cv2.WINDOW_NORMAL)
  cv2.imshow('Annotated image', img.img_rgb)
  cv2.waitKey(0)
  cv2.destroyAllWindows()

  sys.exit(0)


if __name__ == "__main__":
  main(sys.argv[1:])
