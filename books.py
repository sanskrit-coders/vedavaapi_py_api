from PIL import ImageFile
from flask import *
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from common import *
from flask_helper import gen_error_response, myresult
from indicdocs import *

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
      binfo = {'books': getdb().books.list(pattern)}
      return myresult(binfo)
    else:
      return redirect(url_for('index'))
  else:
    return redirect(url_for('index'))


@books_api.route('/get', methods=['GET', 'POST'])
def getbooksingle():
  path = request.args.get('path')
  logging.info("book get by path = " + str(path))
  binfo = getdb().books.get(path)
  # pprint(binfo)
  return myresult(binfo)


@books_api.route('/page/anno/segment/<anno_id>', methods=['GET', 'POST'])
def getpagesegment(anno_id):
  if request.method == 'GET':
    """return the page annotation with id = anno_id"""
    getdb().annotations.segment(anno_id)
    anno = getdb().annotations.get(anno_id)
    return myresult(anno)


@books_api.route('/page/anno/<anno_id>', methods=['GET', 'POST'])
def pageanno(anno_id):
  if request.method == 'GET':
    """return the page annotation with id = anno_id"""
    reparse = json.loads(request.args.get('reparse'))
    if reparse:
      getdb().annotations.propagate(anno_id)
    anno = getdb().annotations.get(anno_id)
    return myresult(anno)
  elif request.method == 'POST':
    """modify/update the page annotation with id = anno_id"""
    anno = request.form.get('anno')
    logging.info("save page annotations by id = " + str(anno_id))
    # logging.info("save page annotations = " + anno)
    anno = json.loads(anno)
    res = getdb().annotations.update(anno_id, {'anno': anno})
    if res == True:
      x = myresult("Annotation saved successfully.")
    else:
      x = gen_error_response("error saving annotation.")
    return x


@books_api.route('/page/sections', methods=['GET', 'POST'])
def getpagesections():
  myid = request.args.get('id')
  sec = getdb().sections.get(myid)
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
@login_required
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
  logging.info("uploading to " + abspath)
  try:
    createdir(abspath)
  except Exception as e:
    error_obj = gen_error_response("Couldn't create upload directory: {}".format(abspath), e)
    logging.error(error_obj)
    return error_obj

  logging.info("User Id: " + current_user.get_id())
  bookpath = abspath.replace(repodir() + "/", "")
  book = getdb().books.get(bookpath)
  if (book is None):
    book = {
      'path': bookpath,
      'pages': [],
      'user': current_user.get_id()
    }
  else:
    del book['_id']
  if (not form.get("author")): book['author'] = form.get("author")
  if (not form.get("title")): book['title'] = form.get("title")
  if (not form.get("pubdate")): book['pubdate'] = form.get("pubdate")
  if (not form.get("scantype")): book['scantype'] = form.get("scantype")
  if (not form.get("bgtype")): book['bgtype'] = form.get("bgtype")
  if (not form.get("language")): book['language'] = form.get("language")
  if (not form.get("script")): book['script'] = form.get("script")

  head, tail = os.path.split(abspath)

  pages = book['pages']
  for upload in request.files.getlist("file"):
    if file and allowed_file(upload.filename):
      filename = secure_filename(upload.filename)
    filename = upload.filename.rsplit("/")[0]
    destination = join(abspath, filename)
    upload.save(destination)
    [fname, ext] = os.path.splitext(filename);
    newFileName = fname + ".jpg";
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

    page = {'tname': thumbnailname, 'fname': newFileName, 'anno': []}
    pages.append(page)

  book['pages'] = pages

  book_mfile = join(abspath, "book.json")
  try:
    with open(book_mfile, "w") as f:
      f.write(json.dumps(book, indent=4, sort_keys=True))
  except Exception as e:
    return gen_error_response("Error writing " + book_mfile + " : ".format(e))

  if (getdb().books.importOne(book) == 0):
    return gen_error_response("Error saving book details.")

  response_msg = "Book upload Successful for " + bookpath
  return myresult(response_msg)
