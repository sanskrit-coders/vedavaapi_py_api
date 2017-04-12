#!/usr/bin/python -u
import datetime
import getopt
from base64 import b64encode
from sys import argv

import logging
from flask import *
from flask_login import LoginManager, login_user, logout_user, \
    current_user

# from file import file_api
from books import books_api
# from flask.ext.cors import CORS
from indicdocs import *
from oauth import *
from oauth import OAuthSignIn

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


app = Flask(__name__)

app.register_blueprint(books_api, url_prefix='/books')

app.config['SECRET_KEY'] = b64encode(os.urandom(24)).decode('utf-8')
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '1706950096293019',
        'secret': '1b2523ac7d0f4b7a73c410b2ec82586c'
    },
    'twitter': {
        'id': 'jSd7EMZFTQlxjLFG4WLmAe2OX',
        'secret': 'gvkh9fbbnKQXXbnqxfs8C0tCEqgNKKzoYJAWQQwtMG07UOPKAj'
    }
}

lm = LoginManager(app)
lm.login_view = 'index'


class User(object):
    def __init__(self, user_id, nickname="Guest", email=None, confirmed_on=False):
        self.user_id = user_id
        self.nickname = nickname
        self.email = email
        self.confirmed_on = confirmed_on

    def is_authenticated(self):
        if self.nickname == 'Guest' and self.confirmed_on == True:
            logging.info("Confirmed=" + str( self.confirmed_on))
            return True

    def is_active(self):
        if self.confirmed_on == True:
            return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.user_id


def authorized_work(required_url, default_url):
    if 'logstatus' in session:
        logging.info("Session Logstatus " + str( session['logstatus']))
        if session['logstatus'] == 1:
            return render_template(required_url, title='Home')
        else:
            logging.info("No-logstatus\n\n")
            return redirect(url_for(default_url))
    else:
        return redirect(url_for(default_url))


@app.route('/homepage')
def mainpage():
    return authorized_work('home.html', 'index')


@lm.user_loader
def load_user(id):
    u = getdb().users.get(id)
    if not u:
        return None
    return User(u['_id'], u['nickname'])


@app.route('/')
def index():
    return render_template('index.html', title='Login')
    # return render_template('home.html', title='Home')


@app.route('/logout')
def logout():
    # obj = OAuthSignIn('facebook')
    # payload = {'grant_type': 'client_credentials', 'client_id': obj.consumer_id, 'client_secret': obj.consumer_secret}
    # resp = requests.post('https://graph.facebook.com/oauth/access_token?', params = payload)
    # result = resp.text.split("=")[1]
    # logging.info("result=" + str(result))
    # session.pop('social_id',None)
    session['logstatus'] = 0
    session['user'] = None
    logout_user()
    # current_user.authenticated=False
    flash("Logged out successfully!", 'info')
    return redirect(url_for('index'))


@app.route('/guestlogin', methods=['GET', 'POST'])
def guestlogin():
    logging.info("Login using Guest....\n")
    email = request.args.get('usermail')
    logging.info("email=" + str( email))
    user = getdb().users.insert(
        {"nickname": "Guest", "email": str(email), "confirmed": True, "confirmed_on": str(datetime.datetime.now())})
    user = User(user['_id'], user['nickname'], user['email'], user['confirmed'])
    if user.is_authenticated():
        session['user'] = 'Guest'
        logging.info("guest user!")
        session['logstatus'] = 1
        return redirect(url_for('mainpage'))
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
        # return redirect(url_for('mainpage'))
    session['logstatus'] = 0
    session['user'] = None
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('mainpage'))
    oauth = OAuthSignIn.get_provider(provider)
    seq = oauth.callback()
    logging.info("Return Value = " + str( seq))
    if (len(seq) == 3):
        social_id, username, email = seq
        logflag = 1
    else:
        social_id, username, email, logflag = seq
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = getdb().users.getBySocialId(social_id)
    if not user:
        user = getdb().users.insert({"social_id": social_id, "nickname": username, "email": email})
    user = User(user['_id'], user['nickname'])
    session['logstatus'] = logflag
    login_user(user, True)
    return redirect(url_for('mainpage'))


@app.route('/<filename>')
def root(filename):
    return app.send_static_file(filename)


@app.route('/abspath/<path:filepath>')
def readabs(filepath):
    abspath = "/" + filepath
    # logging.info("final-path:" + str(abspath))
    head, tail = os.path.split(abspath)
    return send_from_directory(head, tail)


@app.route('/relpath/<path:relpath>')
def readrel(relpath):
    return (send_from_directory(workdir(), relpath))


@app.route('/browse/<path:relpath>')
def browsedir(relpath):
    fullpath = join(workdir(), relpath)
    logging.info(fullpath)
    return render_template("fancytree.html", abspath=fullpath)


# @app.route('/<path:abspath>')
# def details_dir(abspath):
#	logging.info("abspath:" + str(abspath))
#	return render_template("fancytree.html", abspath='/'+abspath)

@app.route('/dirtree/<path:abspath>')
def listdirtree(abspath):
    # print abspath
    data = list_dirtree("/" + abspath)
    # logging.info("Data:" + str(json.dumps(data)))
    return json.dumps(data)


@app.route('/taillog/<string:nlines>/<path:filepath>')
def getlog(nlines, filepath):
    lpath = join(repodir(), filepath)
    logging.info("get logfile " + lpath)
    p = subprocess.Popen(['tail', '-' + nlines, lpath], shell=False,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    p_stdout = p.stdout.read()
    # print p_stdout
    return '''
        <html>
        <meta http-equiv="refresh" content="15">
        <head>
        </head>
        <body>
        <h1>Reading log file ''' + filepath + '''...</h1>
        <div id="scbar" style="border:1px solid black;height:350px;width:600px;overflow-y:auto;white-space:pre"><p>''' + p_stdout + '''</p>
        </div>
        </body>
        </html>
        '''


(cmddir, cmdname) = os.path.split(argv[0])
setmypath(os.path.abspath(cmddir))
logging.info("My path is " + mypath())


def usage():
    logging.info(cmdname + " [-r] [-R] [-d] [-o <workdir>] [-l <local_wloads_dir>] <repodir1>[:<reponame>] ...")
    exit(1)


parms = DotDict({
    'reset': False,
    'dbreset': False,
    'dbgFlag': False,
    'myport': PORTNUM,
    'localdir': None,
    'wdir': workdir(),
    'repos': [],
})


def setup_app(parms):
    setworkdir(parms.wdir, parms.myport)
    logging.info(cmdname + ": Using " + workdir() + " as working directory.")

    initworkdir(parms.reset)

    initdb(INDICDOC_DBNAME, parms.dbreset)

    for a in parms.repos:
        components = a.split(':')
        if len(components) > 1:
            logging.info("Importing " + components[0] + " as " + components[1])
            addrepo(components[0], components[1])
        else:
            logging.info("Importing " + components[0])
            addrepo(components[0], "")

    if parms.localdir:
        setwlocaldir(parms.localdir)
    if not path.exists(wlocaldir()):
        setwlocaldir(DATADIR_BOOKS)
    os.chdir(workdir())

    # Import all book metadata into the IndicDocs database
    getdb().books.importAll(repodir())


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "do:l:p:rRh", ["workdir=", "wloaddir="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-o", "--workdir"):
            parms.wdir = arg
        elif opt in ("-l", "--wloaddir"):
            parms.localdir = arg
        elif opt in ("-p", "--port"):
            parms.myport = int(arg)
        elif opt in ("-r", "--reset"):
            parms.reset = True
        elif opt in ("-R", "--dbreset"):
            parms.dbreset = True
        elif opt in ("-d", "--debug"):
            parms.dbgFlag = True
    parms.repos = args

    setup_app(parms)

    logging.info("Available on the following URLs:")
    for line in mycheck_output(["/sbin/ifconfig"]).split("\n"):
        m = re.match('\s*inet addr:(.*?) .*', line)
        if m:
            logging.info("    http://" + m.group(1) + ":" + str(parms.myport) + "/")
    app.run(
        host="0.0.0.0",
        port=parms.myport,
        debug=parms.dbgFlag,
        use_reloader=False
    )


if __name__ == "__main__":
    main(sys.argv[1:])
else:
    setup_app(parms)
