from PIL import ImageFile
from flask import *
from flask_login import current_user
from werkzeug.utils import secure_filename

from backend import data_containers
from backend.collections import *
import backend.data_containers
from backend.db import get_db
from common import *
from flask_helper import gen_error_response, myresult

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

app = Flask(__name__)

ImageFile.LOAD_TRUNCATED_IMAGES = True
books_api = Blueprint('books_api', __name__)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jp2', 'jpeg', 'gif'])


def allowed_file(filename):
  return '.' in filename and \
         filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@books_api.route('/list', methods=['GET', 'POST'])
def getbooklist():
  logging.info("Session in books_api=" + str(session['logstatus']))
  if 'logstatus' in session:
    if session['logstatus'] == 1:
      pattern = request.args.get('pattern')
      logging.info("books list filter = " + str(pattern))
      binfo = {'books': get_db().books.list(pattern)}
      return myresult(binfo)
    else:
      return redirect(url_for('index'))
  else:
    return redirect(url_for('index'))


@books_api.route('/get', methods=['GET', 'POST'])
def getbooksingle():
  path = request.args.get('path')
  logging.info("book get by path = " + str(path))
  binfo = get_db().books.get(path)
  # pprint(binfo)
  return myresult(binfo)


@books_api.route('/page/anno/segment/<anno_id>', methods=['GET', 'POST'])
def getpagesegment(anno_id):
  if request.method == 'GET':
    """return the page annotation with id = anno_id"""
    get_db().annotations.segment(anno_id)
    anno = get_db().annotations.get(anno_id)
    return myresult(anno)


@books_api.route('/page/anno/<anno_id>', methods=['GET', 'POST'])
def pageanno(anno_id):
  if request.method == 'GET':
    """return the page annotation with id = anno_id"""
    reparse = json.loads(request.args.get('reparse'))
    if reparse:
      get_db().annotations.propagate(anno_id)
    anno = get_db().annotations.get(anno_id)
    return myresult(anno)
  elif request.method == 'POST':
    """modify/update the page annotation with id = anno_id"""
    anno = request.form.get('anno')
    logging.info("save page annotations by id = " + str(anno_id))
    # logging.info("save page annotations = " + anno)
    anno = json.loads(anno)
    res = get_db().annotations.update(anno_id, {'anno': anno})
    if res == True:
      x = myresult("Annotation saved successfully.")
    else:
      x = gen_error_response("error saving annotation.")
    return x


@books_api.route('/page/sections', methods=['GET', 'POST'])
def getpagesections():
  myid = request.args.get('id')
  sec = get_db().sections.get(myid)
  return myresult(sec)


@books_api.route('/page/image/<path:pagepath>')
def getpagesingle(pagepath):
  # abspath = join(repodir(), pagepath)
  # head, tail = os.path.split(abspath)
  return send_from_directory(repodir(), pagepath)


@books_api.route('/browse/<path:bookpath>')
def browsedir(bookpath):
  fullpath = join(repodir(), bookpath)
  return render_template("fancytree.html", abspath=fullpath)


@books_api.route('/delete', methods=['GET', 'POST'])
def delbook():
  return wl_batchprocess(request.args, "delete", wldelete)


@books_api.route('/view', methods=['GET', 'POST'])
def docustom():
  if 'logstatus' in session:
    if session['logstatus'] == 1:
      return render_template("viewbook.html", \
                             bookpath=request.args.get('path'), title="Explore a Book")
    else:
      return redirect(url_for('index'))
  else:
    return redirect(url_for('index'))


@books_api.route('/upload', methods=['GET', 'POST'])
# @login_required TODO: Code fails if this is uncommented.
def upload():
  """Handle uploading files."""
  form = request.form
  logging.info("uploading " + str(form))
  bookpath = (form.get('uploadpath')).replace(" ", "_")

  abspath = join(repodir(), bookpath) if (bookpath.startswith(wlocalprefix())) \
    else join(uploaddir(), bookpath)
  logging.info("uploading to " + abspath)
  try:
    createdir(abspath)
  except Exception as e:
    error_obj = gen_error_response("Couldn't create upload directory: {}".format(abspath), e)
    logging.error(error_obj)
    return error_obj

  if current_user is None:
    user_id = None
  else:
    user_id = current_user.get_id()

  logging.info("User Id: " + str(user_id))
  bookpath = abspath.replace(repodir() + "/", "")

  book = data_containers.BookPortion.from_path(get_db().books, bookpath)

  if (not form.get("title")): book.title = form.get("title")
  if (not form.get("author")): book.authors = [form.get("author")]

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

    # Obsolete:
    # page = {'tname': thumbnailname, 'fname': newFileName, 'anno': []}
    page = backend.JsonObjectNode.from_details(content=data_containers.BookPortion.from_details(title = "pg_%000d" % page_index, path=newFileName))
    pages.append(page)

  book['pages'] = pages

  book_portion_node = data_containers.JsonObjectNode.from_details(content=book, children=pages)

  book_mfile = join(abspath, "book_v2.json")
  try:
    with open(book_mfile, "w") as f:
      f.write(str(book_portion_node))
  except Exception as e:
    return gen_error_response("Error writing " + book_mfile + " : ".format(e))

  try:
    book_portion_node.update_collection(get_db().books)
  except Exception as e:
    return gen_error_response("Error saving book details." + " : ".format(e))

  response_msg = "Book upload Successful for " + bookpath
  return myresult(response_msg)
