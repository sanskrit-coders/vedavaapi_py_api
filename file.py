from flask import *
from werkzeug import secure_filename

from pymongo import MongoClient
from bson.objectid import ObjectId
import json

from gridfs.errors import NoFile
from bookManager import *

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
MYDB = IndicDocDB(INDICDOC_DBNAME)
mybooks = Books(MYDB)

LOG_LEVEL=1

file_api = Blueprint('file_api', __name__)


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@file_api.route('/files', methods=['GET','POST'])
def list_gridfs_files():
    files = [MYDB.get_last_version(file) for file in MYDB.list()]
    file_list = [{'url':url_for('serve_canvas_file',oid=str(file._id)), 'name':file.name} for file in files]
    return render_template("listfiles.html",file_list=file_list,url=url_for('upload_file'))

@file_api.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if not (MYDB.exists(filename=filename)):
                oid = MYDB.put(file, content_type=file.content_type,
                             filename=filename, literal="[]")
                return render_template("drawcanvas.html", oid=str(oid), shapes="[]")
    return render_template("uploadfile.html",url='/file/files')


@file_api.route('/app/<oid>', methods=['GET','POST'])
def serve_canvas_file(oid):
    try:
        file_object = MYDB.get(ObjectId(oid))
        if request.method == 'POST':
            blob = request.form['Blob']
            if LOG_LEVEL > 0 : print('String Blob: ' + blob)
            shapes = json.loads(blob);
            if LOG_LEVEL > 0: print('Shapes Length: ',len(shapes))
            if LOG_LEVEL > 0: print('Filename:', file_object.filename)
            MYDB.insert_literals(ObjectId(oid),shapes)        
             
            return render_template("drawcanvas.html", oid=str(oid), shapes=json.dumps(shapes))
        result = MYDB.find_literals(ObjectId(oid))
        if (result.count() > 0):
            return render_template("drawcanvas.html", oid=str(oid), shapes=json.dumps(result[0]['data']))
        else:
            return render_template("drawcanvas.html", oid=str(oid), shapes="[]")
    except:
        if LOG_LEVEL > 0: print("OID {} not found".format(oid))
        return render_template("uploadfile.html",url=url_for('list_gridfs_files'))


@file_api.route('/files/<oid>')
def serve_gridfs_file(oid):
    try:
        # Convert the string to an ObjectId instance
        file_object = MYDB.get(ObjectId(oid))
          
        response = make_response(file_object.read())
        response.mimetype = file_object.content_type
        return response
    except NoFile:
        if LOG_LEVEL > 0: print("OID {} not found".format(oid))
        return render_template("uploadfile.html",url=url_for('list_gridfs_files'))
    except:
        if LOG_LEVEL > 0: print("OID {} not found".format(oid))
        return render_template("uploadfile.html",url=url_for('list_gridfs_files'))
