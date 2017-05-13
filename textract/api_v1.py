import copy
import traceback
from os.path import join

import flask

from common import flask_helper
import flask_restplus
from flask_login import current_user
from werkzeug.utils import secure_filename

import common.data_containers
from backend.collections import *
from backend.db import get_db
from backend.paths import createdir
from common import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

app = flask_helper.app
URL_PREFIX = '/textract/v1'
api = flask_restplus.Api(app, version='1.0', prefix=URL_PREFIX, title='vedavaapi py API',
                         description='vedavaapi py API', doc= URL_PREFIX + '/doc/')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jp2', 'jpeg', 'gif'])


def allowed_file(filename):
  return '.' in filename and \
         filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


class BookList(flask_restplus.Resource):
  def get(self):
    logging.info("Session in books_api=" + str(session['logstatus']))
    pattern = request.args.get('pattern')
    logging.info("books list filter = " + str(pattern))
    booklist = get_db().books.list_books(pattern)
    logging.debug(booklist)
    return common.data_containers.JsonAjaxResponse(result=booklist).to_json_map_via_pickle()

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
      error_obj = common.data_containers.JsonAjaxErrorResponse(status="Couldn't create upload directory: %s , %s" % (format(abspath), str(e))).to_flask_response()
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

      page = common.data_containers.JsonObjectNode.from_details(
        content=data_containers.BookPortion.from_details(
          title = "pg_%000d" % page_index, path=os.path.join(book.path, newFileName)))
      pages.append(page)

    book_portion_node = common.data_containers.JsonObjectNode.from_details(content=book, children=pages)

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
    return common.data_containers.JsonAjaxResponse(result=response_msg).to_json_map_via_pickle(), 201

api.add_resource(BookList, '/books')


class BookPortionHandler(flask_restplus.Resource):
  def get(self, book_id):
    logging.info("book get by id = " + str(book_id))
    book_portions_collection = get_db().books.db_collection
    book_portion = common.data_containers.JsonObject.from_id(id=book_id, collection=book_portions_collection)
    if book_portion == None:
      return "No such book portion id", 404
    else:
      book_node = common.data_containers.JsonObjectNode.from_details(content=book_portion)
      book_node.fill_descendents(some_collection=book_portions_collection)
      # pprint(binfo)
      return common.data_containers.JsonAjaxResponse(result=book_node).to_json_map_via_pickle(), 200


api.add_resource(BookPortionHandler, '/books/<string:book_id>')


class PageAnnotationsHandler(flask_restplus.Resource):
  def get(self, page_id):
    logging.info("page get by id = " + str(page_id))
    book_portions_collection = get_db().books.db_collection
    page = common.data_containers.JsonObject.from_id(id=page_id, collection=book_portions_collection)
    if page == None:
      return "No such book portion id", 404
    else:
      image_annotations = get_db().annotations.update_image_annotations(page)
      return common.data_containers.JsonAjaxResponse(result=image_annotations).to_json_map_via_pickle(), 200


api.add_resource(PageAnnotationsHandler, '/pages/<string:page_id>/all_segments')


# @flask_blueprint.route('/page/anno/<anno_id>', methods=['GET', 'POST'])
def pageanno(anno_id):
  if request.method == 'GET':
    """return the page annotation with id = anno_id"""
    reparse = json.loads(request.args.get('reparse'))
    if reparse:
      get_db().annotations.propagate(anno_id)
    anno = get_db().annotations.get(anno_id)
    return common.data_containers.JsonAjaxResponse(result=anno).to_flask_response()
  elif request.method == 'POST':
    """modify/update the page annotation with id = anno_id"""
    anno = request.form.get('anno')
    logging.info("save page annotations by id = " + str(anno_id))
    # logging.info("save page annotations = " + anno)
    anno = json.loads(anno)
    res = get_db().annotations.update(anno_id, {'anno': anno})
    if res == True:
      x = common.data_containers.JsonAjaxResponse(result="Annotation saved successfully.").to_flask_response()
    else:
      x = common.data_containers.JsonAjaxErrorResponse(status="error saving annotation.").to_flask_response()
    return x


@app.route('/textract/relpath/<path:relpath>')
def send_file_relpath(relpath):
  return (send_from_directory(paths.DATADIR, relpath))


# @app.route('/<path:abspath>')
# def details_dir(abspath):
#	logging.info("abspath:" + str(abspath))
#	return render_template("fancytree.html", abspath='/'+abspath)

@app.route('/textract/dirtree/<path:abspath>')
def listdirtree(abspath):
  # print abspath
  data = list_dirtree("/" + abspath)
  # logging.info("Data:" + str(json.dumps(data)))
  return json.dumps(data)



