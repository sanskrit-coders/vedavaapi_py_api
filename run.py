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
from bookManager import *

#from file import file_api
from books import books_api

app = Flask(__name__)

app.register_blueprint(books_api, url_prefix='/books')

(cmddir, cmdname) = os.path.split(argv[0])
setmypath(os.path.abspath(cmddir))
print "My path is " + mypath()

def usage():
    print cmdname + " [-r] [-R] [-d] [-o <workdir>] [-l <local_wloads_dir>] <repodir1>[:<reponame>] ..."
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

#@app.route('/<path:abspath>')
#def details_dir(abspath):
#	print "abspath:",abspath
#	return render_template("fancytree.html", abspath='/'+abspath)

@app.route('/dirtree/<path:abspath>')
def listdirtree(abspath):
    #print abspath
    data = list_dirtree("/" + abspath)
    #print "Data:",json.dumps(data)
    return json.dumps(data)

@app.route('/taillog/<string:nlines>/<path:filepath>')
def getlog(nlines, filepath):
    lpath = join(repodir(), filepath)
    print "get logfile " + lpath
    p = subprocess.Popen(['tail','-'+nlines,lpath], shell=False,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    p_stdout=p.stdout.read()
    #print p_stdout
    return '''
        <html>
        <meta http-equiv="refresh" content="15">
        <head>
        </head>
        <body>
        <h1>Reading log file ''' + filepath + '''...</h1>
        <div id="scbar" style="border:1px solid black;height:350px;width:600px;overflow-y:auto;white-space:pre"><p>'''+p_stdout+'''</p>
        </div>
        </body>
        </html>
        '''   

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "do:l:p:rRh", ["workdir=", "wloaddir="])
    except getopt.GetoptError:
        usage()

    reset = False
    dbreset = False
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
        elif opt in ("-R", "--dbreset"):
            dbreset = True
        elif opt in ("-d", "--debug"):
            dbgFlag = True
    setworkdir(wdir,myport)
    print cmdname + ": Using " + workdir() + " as working directory."
    
    initworkdir(reset)

    initdb(INDICDOC_DBNAME, dbreset)

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

    # Import all book metadata into the IndicDocs database
    getdb().books.importAll(repodir())

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
