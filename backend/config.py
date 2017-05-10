import logging
import subprocess
import urllib2

import os
from flask import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

PORTNUM = 9000

INDICDOC_DBNAME = "indicdoc_db"

LOG_LEVEL = 1

SERVER_CONFIG = {}


def serverconfig():
  global SERVER_CONFIG
  return SERVER_CONFIG


def convert(value):
  B = float(value)
  KB = float(1024)
  MB = float(KB ** 2)
  GB = float(KB ** 3)
  TB = float(KB ** 4)
  if (B < KB):
    return '{0} {1}'.format(B, 'Bytes' if 0 == B > 1 else 'B')
  if (KB <= B < MB):
    return '{0:.2f} KB'.format(B / KB)
  if (MB <= B < GB):
    return '{0:.2f} MB'.format(B / MB)
  if (GB <= B < TB):
    return '{0:.2f} GB'.format(B / GB)


def list_dirtree(rootdir):
  all_data = []
  try:
    contents = os.listdir(rootdir)
  except Exception as e:
    logging.error("Error listing " + rootdir + ": " + str(e))
    return all_data
  else:
    for item in contents:
      itempath = os.path.join(rootdir, item)
      info = {}
      children = []
      if os.path.isdir(itempath):
        all_data.append(
          dict(title=item,
               path=itempath,
               folder=True,
               lazy=True,
               key=itempath))
      else:
        fsize = os.path.getsize(itempath)
        fsize = convert(fsize)
        fstr = '[' + fsize + ']'
        all_data.append(dict(title=item + ' ' + fstr, key=itempath))
  return all_data


def run_command(cmd):
  try:
    # shellswitch = isinstance(cmd, collections.Sequence)
    # print "cmd:",cmd
    # print "type:",shellswitch
    shellval = False if (type(cmd) == type([])) else True
    return subprocess.Popen(cmd, shell=shellval,
                            stderr=subprocess.PIPE,
                            stdout=subprocess.PIPE).communicate()[0]
  except Exception as e:
    logging.error("Error in " + cmd + ": " + str(e))
    raise e


# function to check if an input url exists or not(for csv visualizer)
def check(url):
  try:
    urllib2.urlopen(url)
    return True
  except urllib2.HTTPError:
    return False
