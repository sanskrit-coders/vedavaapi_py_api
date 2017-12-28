import logging
import os
from vedavaapi_py_api import run
from sanskrit_data.db.implementations import mongodb

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

REPO_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "textract-example-repo")


def dump_db(dest_dir=os.path.join(REPO_ROOT, "books_v2")):
  from vedavaapi_py_api.ullekhanam.backend import get_db
  db = get_db(db_name_frontend="ullekhanam_test")
  logging.debug(db.list_books())
  db.dump_books(dest_dir)


def main(argv):
  def usage():
    logging.info("run.py [--action dump]...")
    exit(1)

  try:
    opts, args = getopt.getopt(argv, "ha:", ["action="])
    for opt, arg in opts:
      if opt == '-h':
        usage()
      elif opt in ("-a", "--action"):
        params.action = arg
  except getopt.GetoptError:
    usage()

  if params.action == "dump":
    dump_db()
  elif params.action == "import":
    import_db()


if __name__ == '__main__':
  main(sys.argv[1:])