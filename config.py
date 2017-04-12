import os
from os import path
from os.path import *
import re
import sys
import urllib2,getpass
import collections
import subprocess
from json import dumps
from flask import *
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

PORTNUM = 9000
WORKDIR = "/tmp/scan2text"
INDICDOC_DBNAME = "indicdoc_db"
DATADIR = "/opt/scan2text/data"
DATADIR_SETTINGS = join(DATADIR, "settings")
DATADIR_BOOKS = join(DATADIR, "books")
MYPATH = ""
LOG_LEVEL = 1

SERVER_CONFIG = {}

class DotDict(dict):
    def __getattr__(self, name):
        return self[name]

def mypath():
	return MYPATH

def serverconfig():
    global SERVER_CONFIG
    return SERVER_CONFIG

def setmypath(path):
	global MYPATH
	logging.info("Setting my path to " + path)
	MYPATH = path

def cmdpath(cmd):
	#print "Searching " + cmd + " in " + mypath()
	#return cmd
	return join(mypath(), cmd)

def setworkdir(arg,myport=PORTNUM):
    global WORKDIR
    wdir = join(arg,str(myport))
    logging.info("Setting root working directory to " +wdir)
    WORKDIR = wdir

def workdir():
    return WORKDIR

def pubsuffix():
    return "public"

def pubroot():
#    return join(workdir(), pubsuffix())
    return workdir()

def usersuffix(user):
    return join("users", user)

def userroot(user):
    return join(workdir(), usersuffix(user))

def pubdir(dir):
    return join(pubroot(), dir)

def repodir():
    return pubdir("books")

def wlocalprefix():
    return "local"

def wlocaldir():
    return join(repodir(), wlocalprefix())

def setwlocaldir(dir):
    logging.info("Setting local book repository to " + dir)
    addrepo(dir, wlocalprefix())

def uploaddir():
    return join(wlocaldir(), "upload")

def userpath(user, dir):
    return join(userroot(user), dir)

# TODO: Replace these with logging module.
def loglevel():
    return LOG_LEVEL

def log(msg):
    if loglevel() > 0: print(msg)

def createdir(dir):
    if not path.exists(dir):
        logging.info("Creating " + dir + " ...")
        try:
            os.makedirs(dir, 0777)
        except Exception as e:
            logging.error("Error: cannot create directory, aborting.\n" + str(e))
            sys.exit(1)

def initworkdir(reset):
    if (reset):
        logging.info("Clearing previous contents of " + workdir())
        os.system("rm -rf " + workdir());

    logging.info("Initializing work directory ...")
    createdir(workdir())
    createdir(pubroot())
#    createdir(workdir() + "/users")
    createdir(DATADIR_SETTINGS)
    cfgfile = join(DATADIR_SETTINGS, "server_config.json")
    if reset:
        logging.info("Resetting server configuration to defaults")
        os.system("rm -f " + cfgfile)
    if not os.path.exists(cfgfile):
        if os.path.exists(cmdpath("server_config.json")):
            logging.info("Importing derived metric definitions from" + cmdpath("server_config.json"))
            os.system("cp -a " + cmdpath("server_config.json") + " " + cfgfile)
    logging.info("Loading server configuration from " + cfgfile)
    with open(cfgfile, "r") as f:
        global SERVER_CONFIG
        SERVER_CONFIG = json.load(f)
    logging.info("Configuration Settings: ")
    logging.info(json.dumps(SERVER_CONFIG, indent=4))
    logging.info("done.")

def addrepo(d, reponame):
    if not isdir(d):
        return
    head, book = os.path.split(d)

    target = join(repodir(), reponame if reponame else book)
    createdir(dirname(target))
    if isdir(target) and not islink(target):
        logging.warn("Cannot create symlink: target " + target + " exists.")
        return
    if exists(target):
        os.remove(target)
    cmd = "ln -s " + realpath(d) + " " + target
    os.system(cmd)

def convert(value):
    B=float(value)
    KB = float(1024)
    MB = float(KB ** 2)
    GB = float(KB ** 3)
    TB = float(KB ** 4)
    if(B < KB ):
        return '{0} {1}'.format(B,'Bytes' if 0== B>1 else 'B')
    if(KB <= B<MB):
        return '{0:.2f} KB'.format(B/KB)
    if(MB <= B<GB):
        return '{0:.2f} MB'.format(B/MB)
    if(GB <= B<TB):
        return '{0:.2f} GB'.format(B/GB)

def list_dirtree(rootdir):
    all_data = []
    try: 
        contents = os.listdir(rootdir)
    except Exception as e:
        logging.error("Error listing "+rootdir+": " + e)
        return all_data
    else:
        for item in contents:
            itempath = os.path.join(rootdir, item)
            info = {}
            children=[]
            if os.path.isdir(itempath):
                all_data.append( \
                    dict(title=item, \
                         path=itempath, \
                         folder=True, \
                         lazy=True, \
                         key=itempath))
            else:
                fsize = os.path.getsize(itempath)
                fsize = convert(fsize)
                fstr = '['+fsize+']'
                all_data.append(dict(title=item+' '+fstr,key=itempath))
    return all_data

def mycheck_output(cmd):
    try:
        #shellswitch = isinstance(cmd, collections.Sequence)
        #print "cmd:",cmd
        #print "type:",shellswitch
        shellval = False if (type(cmd) == type([])) else True
        return subprocess.Popen(cmd, shell=shellval, \
                stderr=subprocess.PIPE, \
                stdout=subprocess.PIPE).communicate()[0]
    except Exception as e:
        logging.error("Error in " + cmd + ": " + e)
        return "error"

def gen_response(status = 'ok', result = None):
    retobj = {}
    retobj = { 'status' : status }
    if not result is None:
        retobj['result'] = result
    return make_response(json.dumps(retobj))
    #return json.dumps(retobj)
    
def myerror(msg):
    return gen_response(status = msg)
    
def myresult(res = None):
    return gen_response(result = res)

#function to check if an input url exists or not(for csv visualizer)
def check(url):
	try:
		urllib2.urlopen(url)
		return True
	except urllib2.HTTPError:
		return False
