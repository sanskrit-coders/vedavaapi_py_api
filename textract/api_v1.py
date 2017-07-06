import copy
import traceback
from os.path import join

import flask_restplus
from flask_login import current_user
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

import backend.data_containers as backend_data_containers
import common.data_containers as common_data_containers
from backend.paths import createdir
from textract.backend.db.collections import *
from textract.backend.db import get_db

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

URL_PREFIX = '/v1'
api_blueprint = Blueprint(name='textract_api', import_name=__name__)
api = flask_restplus.Api(app=api_blueprint, version='1.0', title='vedavaapi py API',
                         description='vedavaapi py API. Report issues <a href="https://github.com/vedavaapi/vedavaapi_py_api">here</a>. '
                                     'For a list of JSON schema-s this API uses (referred to by name in docs) see <a href="schemas"> here</a>. <BR>'
                                     'A list of REST and non-REST API routes avalilable on this server: <a href="../sitemap">sitemap</a>.  ',
                         prefix=URL_PREFIX, doc='/docs')

# api = flask_restplus.Api(app, version='1.0', prefix=URL_PREFIX, title='vedavaapi py API',
#                          description='vedavaapi py API', doc= URL_PREFIX + '/docs/')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jp2', 'jpeg', 'gif'])

json_node_model = api.model('JsonObjectNode', common_data_containers.JsonObjectNode.schema)


@api.route('/books')
class BookList(flask_restplus.Resource):
  # Marshalling as below does not work.
  # @api.marshal_list_with(json_node_model)
  def get(self):
    """ Get booklist.
    
    :return: a list of JsonObjectNode json-s.
    """
    logging.info("Session in books_api=" + str(session['logstatus']))
    pattern = request.args.get('pattern')
    logging.info("books list filter = " + str(pattern))
    booklist = get_db().books.list_books(pattern)
    logging.debug(booklist)
    return data_containers.JsonObject.get_json_map_list(booklist), 200

  @classmethod
  def allowed_file(cls, filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

  post_parser = api.parser()
  post_parser.add_argument('in_files', type=FileStorage, location='files')
  post_parser.add_argument('uploadpath', location='form', type='string')
  post_parser.add_argument('title', location='form', type='string')
  post_parser.add_argument('author', location='form', type='string')

  @api.expect(post_parser, validate=True)
  def post(self):
    """Handle uploading files.
    
    :return: Book details in a json tree like:
      {"content": BookPortionObj, "children": [BookPortion_Pg1, BookPortion_Pg2]}    
    """
    form = request.form
    logging.info("uploading " + str(form))
    bookpath = (form.get('uploadpath')).replace(" ", "_")

    abspath = join(paths.DATADIR, bookpath)
    logging.info("uploading to " + abspath)
    try:
      createdir(abspath)
    except Exception as e:
      logging.error(str(e))
      return "Couldn't create upload directory: %s , %s" % (format(abspath), str(e)), 500

    if current_user is None:
      user_id = None
    else:
      user_id = current_user.get_id()

    logging.info("User Id: " + str(user_id))
    bookpath = abspath.replace(paths.DATADIR + "/", "")

    book = (backend_data_containers.BookPortion.from_path(path=bookpath, db_interface=get_db().books) or
            backend_data_containers.BookPortion.from_details(path=bookpath, title=form.get("title")))

    if (not book.authors): book.authors = [form.get("author")]

    pages = []
    page_index = -1
    for upload in request.files.getlist("file"):
      page_index = page_index + 1
      filename = upload.filename.rsplit("/")[0]
      if file and self.__class__.allowed_file(filename):
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

      page = common_data_containers.JsonObjectNode.from_details(
        content=backend_data_containers.BookPortion.from_details(
          title="pg_%000d" % page_index, path=os.path.join(book.path, newFileName)))
      pages.append(page)

    book_portion_node = common_data_containers.JsonObjectNode.from_details(content=book, children=pages)

    book_portion_node_minus_id = copy.deepcopy(book_portion_node)
    book_portion_node_minus_id.content._id = None
    book_mfile = join(abspath, "book_v2.json")
    book_portion_node_minus_id.dump_to_file(book_mfile)

    try:
      book_portion_node.update_collection(get_db().books)
    except Exception as e:
      logging.error(format(e))
      traceback.print_exc()
      return format(e), 500

    return book_portion_node.to_json_map_via_pickle(), 200


@api.route('/books/<string:book_id>')
class BookPortionHandler(flask_restplus.Resource):
  @api.doc(responses={404: 'id not found'})
  def get(self, book_id):
    """ Get a book.
    
    :param book_id: a string. 
    :return: Book details in a json tree like:
      {"content": BookPortionObj, "children": [BookPortion_Pg1, BookPortion_Pg2]}    
    """
    logging.info("book get by id = " + str(book_id))
    book_portions_collection = get_db().books
    book_portion = common_data_containers.JsonObject.from_id(id=book_id, db_interface=book_portions_collection)
    if book_portion == None:
      return "No such book portion id", 404
    else:
      book_node = common_data_containers.JsonObjectNode.from_details(content=book_portion)
      book_node.fill_descendents(db_interface=book_portions_collection)
      # pprint(binfo)
      return book_node.to_json_map_via_pickle(), 200


@api.route('/pages/<string:page_id>/image_annotations/all')
class AllPageAnnotationsHandler(flask_restplus.Resource):
  @api.doc(responses={404: 'id not found'})
  def get(self, page_id):
    """ Get all annotations (pre existing or automatically generated from open CV) for this page.
    
    :param page_id: 
    :return: A list of JsonObjectNode-s with annotations with the following structure.
      {"content": ImageAnnotation, "children": [TextAnnotation_1]}    
    """
    logging.info("page get by id = " + str(page_id))
    book_portions_collection = get_db().books
    page = common_data_containers.JsonObject.from_id(id=page_id, db_interface=book_portions_collection)
    if page == None:
      return "No such book portion id", 404
    else:
      image_annotations = get_db().annotations.update_image_annotations(page)
      image_annotation_nodes = [common_data_containers.JsonObjectNode.from_details(content=annotation) for annotation in
                                image_annotations]
      for node in image_annotation_nodes:
        node.fill_descendents(db_interface=get_db().annotations)
      return common_data_containers.JsonObject.get_json_map_list(image_annotation_nodes), 200


@api.route('/pages/<string:page_id>/image_annotations')
class PageAnnotationsHandler(flask_restplus.Resource):
  # input_node = api.model('JsonObjectNode', common_data_containers.JsonObjectNode.schema)

  post_parser = api.parser()
  post_parser.add_argument('jsonStr', location='json')

  # TODO: The below fails. Await response on https://github.com/noirbizarre/flask-restplus/issues/194#issuecomment-284703984 .
  # @api.expect(json_node_model, validate=False)

  @api.expect(post_parser, validate=False)
  def post(self, page_id):
    """ Add annotations.
    
    :param page_id: The page being annotated. Unused. <BR>
    json:<BR>
      A list of JsonObjectNode-s with annotations with the following structure.
      {"content": ImageAnnotation, "children": [TextAnnotation_1]}    
    :return: 
      Same as the input list, with _id-s.
    """
    logging.info(str(request.json))
    nodes = common_data_containers.JsonObject.make_from_dict_list(request.json)
    # logging.info(jsonpickle.dumps(nodes))
    for node in nodes:
      node.update_collection(db_interface=get_db().annotations)
    return common_data_containers.JsonObject.get_json_map_list(nodes), 200

  @api.expect(post_parser, validate=False)
  def delete(self, page_id):
    """ Delete annotations.
    
    :param page_id: The page being annotated. Unused. 
    json:
      A list of JsonObjectNode-s with annotations with the following structure.
      {"content": ImageAnnotation, "children": [TextAnnotation_1]}    
    :return: Empty.
    """
    nodes = common_data_containers.JsonObject.make_from_dict_list(request.json)
    for node in nodes:
      node.fill_descendents(db_interface=get_db().annotations)
      node.delete_in_collection(db_interface=get_db().annotations)
    return {}, 200


@api_blueprint.route('/relpath/<path:relpath>')
def send_file_relpath(relpath):
  """Get some data file - such as a page image."""
  return (send_from_directory(paths.DATADIR, relpath))


# @app.route('/<path:abspath>')
# def details_dir(abspath):
#	logging.info("abspath:" + str(abspath))
#	return render_template("fancytree.html", abspath='/'+abspath)

@api_blueprint.route('/dirtree/<path:abspath>')
def listdirtree(abspath):
  """???."""
  # print abspath
  data = list_dirtree("/" + abspath)
  # logging.info("Data:" + str(json.dumps(data)))
  return json.dumps(data)


@api_blueprint.route('/schemas')
def list_schemas():
  """???."""
  schemas = {
    "JsonObject": common_data_containers.JsonObject.schema,
    "JsonObjectNode": common_data_containers.JsonObjectNode.schema,
    "BookPortion": backend_data_containers.BookPortion.schema,
    "ImageAnnotation": backend_data_containers.ImageAnnotation.schema,
    "TextAnnotation": backend_data_containers.TextAnnotation.schema,
  }
  return jsonify(schemas)
