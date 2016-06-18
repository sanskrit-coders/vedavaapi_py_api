#!/usr/bin/python -u
import os
from os import walk, path
from os.path import splitext, join
import sys, getopt
import re
import glob
import csv
from sys import argv
from flask import *
from json import dumps
from werkzeug import secure_filename
import subprocess
#from flask.ext.cors import CORS
from config import *

from file import file_api
from books import books_api

app = Flask(__name__)

app.register_blueprint(file_api, url_prefix='/file')
app.register_blueprint(books_api, url_prefix='/books')

(cmddir, cmdname) = os.path.split(argv[0])
setmypath(os.path.abspath(cmddir))
print "My path is " + mypath()

def usage():
    print cmdname + " [-r] [-d] [-o <workdir>] [-l <local_wloads_dir>] <repodir1>[:<reponame>] ..."
    exit(1)

@app.route('/')
def default():
    return render_template('home.html', title='Home')

@app.route('/<filename>')
def root(filename):
    return app.send_static_file(filename)

@app.route('/abspath/<path:filepath>')
def readabs(filepath):
    abspath="/"+filepath
    #print "final-path:",abspath
    head, tail = os.path.split(abspath)
    return send_from_directory(head,tail)

@app.route('/relpath/<path:relpath>')
def readrel(relpath):
    return (send_from_directory(workdir(), relpath))

@app.route('/browse/<path:relpath>')
def browsedir(relpath):
    fullpath = join(workdir(), relpath)
    print fullpath
    return render_template("fancytree.html", abspath=fullpath)

@app.route('/<path:abspath>')
def details_dir(abspath):
	print "abspath:",abspath
	return render_template("fancytree.html", abspath='/'+abspath)

@app.route('/dirtree/<path:abspath>')
def listdirtree(abspath):
    #print abspath
    data = list_dirtree("/" + abspath)
    #print "Data:",json.dumps(data)
    return json.dumps(data)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "do:l:p:rh", ["workdir=", "wloaddir="])
    except getopt.GetoptError:
        usage()

    reset = False
    dbgFlag = False
    myport = PORTNUM
    localdir = None
    wdir = workdir()
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-o", "--workdir"):
	    wdir=arg
        elif opt in ("-l", "--wloaddir"):
            localdir = arg
        elif opt in ("-p", "--port"):
            myport = int(arg)
        elif opt in ("-r", "--reset"):
            reset = True
        elif opt in ("-d", "--debug"):
            dbgFlag = True
    setworkdir(wdir,myport)
    print cmdname + ": Using " + workdir() + " as working directory."
    
    initworkdir(reset)
    for a in args:
        components = a.split(':')
        if len(components) > 1:
            print "Importing " + components[0] + " as " + components[1]
            addrepo(components[0], components[1])
        else: 
            print "Importing " + components[0]
            addrepo(components[0], "")

    if localdir:
        setwlocaldir(localdir)
    if not path.exists(wlocaldir()):
        setwlocaldir(DATADIR_BOOKS)
    os.chdir(workdir())

    print "Available on the following URLs:"
    for line in mycheck_output(["/sbin/ifconfig"]).split("\n"):
        m = re.match('\s*inet addr:(.*?) .*', line)
        if m:
            print "    http://" + m.group(1) + ":" + str(myport) + "/"
    app.run(
      host ="0.0.0.0",
      port = myport,
      debug = dbgFlag,
      use_reloader=False
     )

if __name__ == "__main__":
   main(sys.argv[1:])