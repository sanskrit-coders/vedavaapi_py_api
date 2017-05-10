import copy
import traceback

import flask_restful
from PIL import ImageFile
from flask import *
from flask_login import current_user
from os.path import join
from werkzeug.utils import secure_filename

import backend.data_containers
from backend.collections import *
from backend.db import get_db
from backend import paths
from backend.paths import createdir
from common import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

app = Flask(__name__)
api = flask_restful.Api(app=app, prefix='/api_v1')

ImageFile.LOAD_TRUNCATED_IMAGES = True
flask_blueprint = Blueprint('flask_api', __name__)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jp2', 'jpeg', 'gif'])


def allowed_file(filename):
  return '.' in filename and \
         filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


class BookList(flask_restful.Resource):
  def get(self):
    logging.info("Session in books_api=" + str(session['logstatus']))
    pattern = request.args.get('pattern')
    logging.info("books list filter = " + str(pattern))
    booklist = get_db().books.list_books(pattern)
    logging.debug(booklist)
    return backend.data_containers.JsonAjaxResponse(result=booklist).to_json_map_via_pickle()

  def post(self):
    """Handle uploading files."""
    form = request.form
    logging.info("uploading " + str(form))
    bookpath = (form.get('uploadpath')).replace(" ", "_")

    abspath = join(paths.DATADIR, bookpath)
    logging.info("uploading to " + abspath)
    try:
      createdir(abspath)
    except Exception as e:
      error_obj = backend.data_containers.JsonAjaxErrorResponse(status="Couldn't create upload directory: %s , %s" % (format(abspath), str(e))).to_flask_response()
      logging.error(error_obj)
      return error_obj

    if current_user is None:
      user_id = None
    else:
      user_id = current_user.get_id()

    logging.info("User Id: " + str(user_id))
    bookpath = abspath.replace(paths.DATADIR + "/", "")

    book = (data_containers.BookPortion.from_path(path=bookpath, collection= get_db().books.db_collection) or
            data_containers.BookPortion.from_details(path=bookpath, title=form.get("title")))

    if (not book.authors): book.authors = [form.get("author")]

    pages = []
    page_index = -1
    for upload in request.files.getlist("file"):
      page_index = page_index + 1
      filename = upload.filename.rsplit("/")[0]
      if file and allowed_file(filename):
        filename = secure_filename(filename)
      destination = join(abspath, filename)
      upload.save(destination)
      [fname, ext] = os.path.splitext(filename)
      newFileName = fname + ".jpg"
      tmpImage = cv2.imread(destination)
      cv2.imwrite(join(abspath, newFileName), tmpImage)

      image = Image.open(join(abspath, newFileName)).convert('RGB')
      workingFilename = os.path.splitext(filename)[0] + "_working.jpg"
      out = file(join(abspath, workingFilename), "w")
      img = DocImage.resize(image, (1920, 1080), False)
      img.save(out, "JPEG", quality=100)
      out.close()

      image = Image.open(join(abspath, newFileName)).convert('RGB')
      thumbnailname = os.path.splitext(filename)[0] + "_thumb.jpg"
      out = file(join(abspath, thumbnailname), "w")
      img = DocImage.resize(image, (400, 400), True)
      img.save(out, "JPEG", quality=100)
      out.close()

      page = data_containers.JsonObjectNode.from_details(
        content=data_containers.BookPortion.from_details(
          title = "pg_%000d" % page_index, path=os.path.join(book.path, newFileName)))
      pages.append(page)

    book_portion_node = data_containers.JsonObjectNode.from_details(content=book, children=pages)

    book_portion_node_minus_id = copy.deepcopy(book_portion_node)
    book_portion_node_minus_id.content._id = None
    book_mfile = join(abspath, "book_v2.json")
    book_portion_node_minus_id.dump_to_file(book_mfile)

    try:
      book_portion_node.update_collection(get_db().books.db_collection)
    except Exception as e:
      logging.error(format(e))
      traceback.print_exc()
      return format(e), 500

    response_msg = "Book upload Successful for " + bookpath
    return backend.data_containers.JsonAjaxResponse(result=response_msg).to_json_map_via_pickle(), 201

api.add_resource(BookList, '/books')


class BookPortionHandler(flask_restful.Resource):
  def get(self, book_id):
    logging.info("book get by id = " + str(book_id))
    book_portions_collection = get_db().books.db_collection
    book_portion = data_containers.JsonObject.from_id(id=book_id, collection=book_portions_collection)
    if book_portion == None:
      return "No such book portion id", 404
    else:
      book_node = data_containers.JsonObjectNode.from_details(content=book_portion)
      book_node.fill_descendents(some_collection=book_portions_collection)
      # pprint(binfo)
      return backend.data_containers.JsonAjaxResponse(result=book_node).to_json_map_via_pickle(), 201


api.add_resource(BookPortionHandler, '/books/<string:book_id>')


@flask_blueprint.route('/<_id>', methods=['GET'])
def getpagesegment(id):
  if request.method == 'GET':
    """return the page annotation with id = anno_id"""
    page = data_containers.JsonObject.from_id(id=id, collection=get_db().books.db_collection)
    page_image = DocImage.from_path(path=page.path)
    # get_db().annotations.segment(anno_id)
    # anno = get_db().annotations.get(anno_id)
    # return backend.data_containers.JsonAjaxResponse(result=anno).to_flask_response()


@flask_blueprint.route('/page/anno/<anno_id>', methods=['GET', 'POST'])
def pageanno(anno_id):
  if request.method == 'GET':
    """return the page annotation with id = anno_id"""
    reparse = json.loads(request.args.get('reparse'))
    if reparse:
      get_db().annotations.propagate(anno_id)
    anno = get_db().annotations.get(anno_id)
    return backend.data_containers.JsonAjaxResponse(result=anno).to_flask_response()
  elif request.method == 'POST':
    """modify/update the page annotation with id = anno_id"""
    anno = request.form.get('anno')
    logging.info("save page annotations by id = " + str(anno_id))
    # logging.info("save page annotations = " + anno)
    anno = json.loads(anno)
    res = get_db().annotations.update(anno_id, {'anno': anno})
    if res == True:
      x = backend.data_containers.JsonAjaxResponse(result="Annotation saved successfully.").to_flask_response()
    else:
      x = backend.data_containers.JsonAjaxErrorResponse(status="error saving annotation.").to_flask_response()
    return x
