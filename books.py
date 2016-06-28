import os
from os import path
from flask import *
from functools import wraps
import json,time
from flask import jsonify
from json import dumps
from werkzeug import secure_filename
from PIL import Image
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

def resize(img, box, fit, out):
    '''Downsample the image.
    @param img: Image -  an Image-object
    @param box: tuple(x, y) - the bounding box of the result image
    @param fix: boolean - crop the image to fill the box
    @param out: file-like-object - save the image into the output stream
    '''
    #preresize image with factor 2, 4, 8 and fast algorithm
    factor = 1
    while img.size[0]/factor > 2*box[0] and img.size[1]*2/factor > 2*box[1]:
        factor *=2

    if factor > 1:
        img.thumbnail((img.size[0]/factor, img.size[1]/factor), Image.ANTIALIAS)

    #calculate the cropping box and get the cropped part
    if fit:
        x1 = y1 = 0
        x2, y2 = img.size
        wRatio = 1.0 * x2/box[0]
        hRatio = 1.0 * y2/box[1]
        if hRatio > wRatio:
            y1 = int(y2/2-box[1]*wRatio/2)
            y2 = int(y2/2+box[1]*wRatio/2)
        else:
            x1 = int(x2/2-box[0]*hRatio/2)
            x2 = int(x2/2+box[0]*hRatio/2)
        img = img.crop((x1,y1,x2,y2))

    #Resize the image with best quality algorithm ANTI-ALIAS
    img.thumbnail(box, Image.ANTIALIAS)

    #save it into a file-like object
    img.save(out, "JPEG", quality=100)
#resize

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
        anno = getdb().annotations.get(anno_id)
        return myresult(anno)
    elif request.method == 'POST':
        """modify/update the page annotation with id = anno_id"""
        anno = request.form.get('anno')
        print "save page annotations by id = " + str(anno_id)
        print "save page annotations = " + json.dumps(anno)
        res = getdb().annotations.update(anno_id, { 'anno' : anno })
        if res == True:
            x = myresult("Annotation saved successfully.")
        else:
            x = myerror("error saving annotation.")
        return x

@books_api.route('/page/sections', methods = ['GET', 'POST'])
def getpagesections():
    myid = request.args.get('id')
    sec = getdb().sections.get(myid)
    return myresult(sec)

@books_api.route('/page/image/<path:pagepath>')
def getpagesingle(pagepath):
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
    abspath = join(repodir(), bookpath) if (bookpath.startswith(wlocalprefix())) \
        else join(uploaddir(), bookpath)
    print "uploading to " + abspath
    try:
        createdir(abspath)
    except Exception as e:
        return myerror("Couldn't create upload directory: {}".format(abspath), e)

    bookpath = abspath.replace(repodir() + "/", "")
    book = { 
        'author' : form.get("author"),
        'title' : form.get("title"),
        'pubdate' : form.get("date"),
        'scantype' : form.get("scantype"),
        'bgtype' : form.get("bgtype"),
        'language' : form.get("language"),
        'script' : form.get("script"),
        'path' : bookpath,
        'pages' : []
    }
    head, tail = os.path.split(abspath)

    pages = []
    for upload in request.files.getlist("file"):
        if file and allowed_file(upload.filename):
            filename = secure_filename(upload.filename)
        filename = upload.filename.rsplit("/")[0]
        destination = join(abspath, filename)
        upload.save(destination)

        image = Image.open(join(abspath, filename)).convert('RGB')
        thumbnailname = os.path.splitext(filename)[0]+"_thumb.jpg"
        out = file(join(abspath, thumbnailname), "w")
        img = resize(image, (400,400), True, out)
        out.close()

        page = { 'tname': thumbnailname, 'fname' : filename, 'anno' : [] }
        pages.append(page)

    book['pages'] = pages

    book_mfile = join(abspath, "book.json")
    try:
        with open(book_mfile, "w") as f:
            f.write(json.dumps(book, indent=4, sort_keys=True))
    except Exception as e:
        return myerror("Error writing " + book_mfile + ":", e)

    if (getdb().books.importOne(book) == 0):
        return myerror("Error saving book details.")

    response_msg = "Book upload Successful for " + bookpath
    return myresult(response_msg)
