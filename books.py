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
from common import *
from uuid import uuid4
import subprocess
import csv
import string
from collections import OrderedDict
from bookManager import *
import traceback
app = Flask(__name__)
from pprint import pprint

books_api = Blueprint('books_api', __name__)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@books_api.route('/list', methods = ['GET', 'POST'])
def getbooklist():
    pattern = request.args.get('pattern')
    print "books list filter = " + str(pattern)
    binfo = {'books' : getdb().books.list(pattern) }
    return myresult(binfo)

@books_api.route('/get', methods = ['GET', 'POST'])
def getbooksingle():
    path = request.args.get('path')
    print "book get by path = " + str(path)
    binfo = getdb().books.get(path)
    #pprint(binfo)
    return myresult(binfo)

@books_api.route('/page/anno/<anno_id>', methods = ['GET', 'POST'])
def pageanno(anno_id):
    if request.method == 'GET':
        """return the page annotation with id = anno_id"""
        print "get page annotations by id " + anno_id
        anno = getdb().annotations.get(anno_id)
        return myresult(anno)
    elif request.method == 'POST':
        """modify/update the page annotation with id = anno_id"""
        anno = request.form['anno']
        print "save page annotations by id = " + str(anno_id)
        pprint(anno)
        res = getdb().annotations.update(anno_id, anno)
        if (res > 0):
            return myresult("Annotation saved successfully.")
        else:
            return myerror("error saving annotation.")

@books_api.route('/page/sections', methods = ['GET', 'POST'])
def getpagesections():
    myid = request.args.get('id')
    print "get page sections by id " + str(myid)
    sec = getdb().sections.get(myid)
    return myresult(sec)

@books_api.route('/page/image/<path:pagepath>')
def getpagesingle(pagepath):
    print "get book page " + pagepath
    #abspath = join(repodir(), pagepath)
    #head, tail = os.path.split(abspath)
    return send_from_directory(repodir(), pagepath)

@books_api.route('/browse/<path:bookpath>')
def browsedir(bookpath):
    fullpath = join(repodir(), bookpath)
    return render_template("fancytree.html",abspath=fullpath)

@books_api.route('/delete', methods = ['GET', 'POST'])
def delbook():
    return wl_batchprocess(request.args, "delete", wldelete)

@books_api.route('/view', methods = ['GET', 'POST'])
def docustom():
    return render_template("viewbook.html", \
            bookpath=request.args.get('path'), title="Explore a Book")

@books_api.route('/upload', methods = ['GET', 'POST'])
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
    head, tail = os.path.split(abspath)

    pages = []
    for upload in request.files.getlist("file"):
        if file and allowed_file(upload.filename):
            filename = secure_filename(upload.filename)
        filename = upload.filename.rsplit("/")[0]
        destination = join(wdir, filename)
        upload.save(destination)
        page = { 'fname' : filename, 'annotations' : [] }
        pages.append(page)

    book.pages = pages

    book_mfile = join(wdir, "book.json")
    try:
        with open(book_mfile, "w") as f:
            f.write(json.dumps(book, indent=4, sort_keys=True))
    except Exception as e:
        return myerror("Error writing " + book_mfile + ":", e)

    if (getdb().books.insert(book) == 0):
        return myerror("Error saving book details.")

    response_msg = "Book upload Successful for " + bookpath
    return myresult(response_msg)
