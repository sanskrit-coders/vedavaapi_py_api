import os
from os import path
from flask import *
from functools import wraps
import json,time
from flask import jsonify
from json import dumps
from werkzeug import secure_filename
import datetime
from config import *
from libpage import *
from uuid import uuid4
import subprocess
import csv
import string
from collections import OrderedDict
import traceback
app = Flask(__name__)
import pprint

page_api = Blueprint('page_api', __name__)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@page_api.route('/propagate')
def default():
    pageoid = request.arg.get("page_oid")
    page_json  = BM.get(pageoid)
    newpage_json = do_propagate(page_json)
    BM.put(pageoid, newpage_json)
    return myresult(newpage_json))
    lpath = join(repodir(), filepath)
    print "get " + lpath
    return send_from_directory(repodir(), filepath)

@page_api.route('/taillog/<string:nlines>/<path:filepath>')
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
#code for book list
@page_api.route('/list', methods = ['GET', 'POST'])
def getwinfo():
    pattern = request.args.get('pattern')
    print "page list filter = " + str(pattern)
    binfo = listpage(pattern)
    return (make_response(dumps(binfo)))

@page_api.route('/browse/<path:bookpath>')
def browsedir(bookpath):
    fullpath = join(repodir(), bookpath)
    return render_template("fancytree.html",abspath=fullpath)

@page_api.route('/delete', methods = ['GET', 'POST'])
def delwload():
    return wl_batchprocess(request.args, "delete", wldelete)

@page_api.route('/view', methods = ['GET', 'POST'])
def docustom():
    return render_template("explore.html", bookname=request.args.get('bookname'))

@page_api.route('/upload', methods = ['GET', 'POST'])
def upload():
    """Handle uploading files."""
    form = request.form
    bookpath = (form.get('uploadpath')).replace(" ", "_")
    # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = False
    if form.get("__ajax", None) == "true":
        is_ajax = True
    wdir = join(repodir(), bookpath) if (bookpath.startswith(wlocalprefix())) \
        else join(uploaddir(), bookpath)
    try:
        createdir(wdir)
    except Exception as e:
        return myerror("Couldn't create upload directory: {}".format(wdir), e)

    book = { 
        'author' : form.get("author"),
        'title' : form.get("title"),
        'pubdate' : form.get("date"),
        'scantype' : form.get("scantype"),
        'bgtype' : form.get("bgtype"),
        'language' : form.get("language"),
        'script' : form.get("script"),
        'pages' : []
    }

    pages = []
    for upload in request.files.getlist("file"):
        if file and allowed_file(upload.filename):
            filename = secure_filename(upload.filename)
        filename = upload.filename.rsplit("/")[0]
        destination = join(wdir, filename)
        upload.save(destination)
        page = { 'fname' : filename, 'annotations' : [] }
        pages.append(page)

    book_mfile = join(wdir, "book.json")
    try:
        with open(book_mfile, "w") as f:
            f.write(json.dumps(book, indent=4, sort_keys=True))
    except Exception as e:
        return myerror("Error writing " + book_mfile + ":", e)

    response_msg = "Upload Successful for:" + bookpath
    return myresult(response_msg)
