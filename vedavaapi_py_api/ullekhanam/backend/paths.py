import logging
import sys

import os
from os import path

DATADIR = "/opt/scan2text/data/books"
CODE_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LOCAL_PREFIX = "local"

def init_data_dir():
  logging.info("Initializing work directory ...")
  createdir(os.path.dirname(DATADIR))


def createdir(dir):
  if not path.exists(dir):
    logging.info("Creating " + dir + " ...")
    try:
      os.makedirs(dir)
    except Exception as e:
      logging.error("Error: cannot create directory, aborting.\n" + str(e))
      sys.exit(1)