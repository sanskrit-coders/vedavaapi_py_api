from bson.objectid import ObjectId
from pymongo.database import Database

from pymongo import MongoClient

from config import *
from docimage import *

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

#from gridfs import GridFS
#from gridfs.errors import NoFile

class Books:
    def __init__(self, indicdocs):
        #print "Initializing books collection ..."
        self.indicdocs = indicdocs
        self.books = indicdocs.db['books']

    def insert(self, book):
        self.books.update({"path" : book["path"]}, book, upsert=True)
        return self.books.find({'path': book["path"]}).count()

    def list(self, pattern=None):
        cursor = self.books.find({}, {'_id' : False, 'pages' : False})
        matches = [b for b in cursor if not pattern or re.search(pattern, b['path'])]
        return matches

    def getPageByIdx(self, book, idx):
        return book.pages[idx]

    def getPageByName(self, book, pagename):
        page = book.find({"pages.fname", pagename})
        return page

    def get(self, path):
        book = self.books.find_one({'path' : path})
        if book is not None:
            book['_id'] = str(book['_id'])
        return book

    def importOne(self, book):
        pgidx = 0
        bpath = book['path']
        if 'user' in book :
            buser = book['user']
        else:
            buser = ""

        for page in book['pages']:
            try:
                anno_id = self.indicdocs.annotations.insert( \
                    { 'bpath' : bpath, 'pgidx' : pgidx, \
                        'anno' : [] , 'user': buser})
                sec_id = self.indicdocs.sections.insert( \
                    { 'bpath' : bpath, 'pgidx' : pgidx, \
                        'sections' : [] , 'user': buser})
                #print "anno: " + str(anno_id) + ", sec: " + str(sec_id)
                page['anno'] = anno_id
                page['sections'] = sec_id
            except Exception as e:
                print "Error inserting anno", e
            #print json.dumps(page, indent=4)
            pgidx = pgidx + 1
        #print json.dumps(book, indent=4)
        self.insert(book)

    def importAll(self, rootdir, pattern = None):
        print "Importing books into database from ", rootdir
        cmd = "find "+rootdir+" \( \( -path '*/.??*' \) -prune \) , \( -path '*.json' \) -follow -print; true"
        try:
            results = mycheck_output(cmd)
        except Exception as e:
            print "Error in find: ", e
            return 0

        nbooks = 0
        for f in results.split("\n"):
            if not f:
                continue
            bpath, fname = os.path.split(f.replace(rootdir + "/", ""))
            print "    "+bpath
            if pattern and not re.search(pattern, bpath, re.IGNORECASE):
                continue
            winfo = {}
            try:
                with open(f) as fhandle:
                    book = json.load(fhandle)
                    #print json.dumps(book, indent=4)
                    book["path"] = bpath
                    if self.get(bpath) is None:
                        self.importOne(book)
                        nbooks = nbooks + 1
            except Exception as e:
                print "Skipped book " + f + ". Error:", e
        return nbooks

class Annotations:
    def __init__(self, indicdocs):
        self.indicdocs = indicdocs
        self.annotations = indicdocs.db['annotations']

    def get(self, anno_id):
        res = self.annotations.find_one({'_id' : ObjectId(anno_id)})
        res['_id'] = str(res['_id'])
        return res

    def get_image(self, anno_id):
        # Get the annotations from anno_id
        anno_obj = self.get(anno_id)
        if not anno_obj:
            return False

        # Get the containing book
        books = self.indicdocs.books
        book = books.get(anno_obj['bpath'])
        if not book:
            return False

        page = book['pages'][anno_obj['pgidx']]
        imgpath = join(repodir(), join(anno_obj['bpath'], page['fname']))
        print "Image path = ", imgpath
        page_img = DocImage(imgpath)
        return page_img

    def insert(self, anno):
        id = self.annotations.insert(anno)
        return str(id)

    def update(self, anno_id, anno):
        #pprint(anno)
        result = self.annotations.update({'_id' : ObjectId(anno_id)}, { "$set": anno })
        isSuccess = (result['n'] > 0)
        return isSuccess

    def segment(self, anno_id):
        # Get the annotations from anno_id
        anno_obj = self.get(anno_id)
        if not anno_obj:
            return False

        # Get the containing book
        books = self.indicdocs.books
        book = books.get(anno_obj['bpath'])
        if not book:
            return False

        page = book['pages'][anno_obj['pgidx']]
        [fname,ext] = os.path.splitext(page['fname']);
        imgpath = join(repodir(), join(anno_obj['bpath'], page['fname']))
        workingImgPath = join(repodir(), join(anno_obj['bpath'], fname+"_working.jpg"))
        print "Image path = ", imgpath
        print "Working Image path = ", workingImgPath
        page_img = DocImage(imgpath, workingImgPath)

        known_segments = DisjointSegments()
        for a in anno_obj['anno']:
            a = ImgSegment(a)
            if a.state == 'system_inferred':
                continue
            a['score'] = float(1.0) # Set the max score for user-identified segments
            # Prevent image matcher from changing user-identified segments
            known_segments.insert(a)

        matches = page_img.find_segments(0,0,known_segments)
        #print "Matches = " + json.dumps(matches)
        #print "Segments = " + json.dumps(known_segments.segments)
        for r in matches:
            # and propagate its text to them
            r['state'] = 'system_inferred'

        self.update(anno_id, { 'anno' : known_segments.segments })
        return True


    def propagate(self, anno_id):
        # Get the annotations from anno_id
        anno_obj = self.get(anno_id)
        if not anno_obj:
            return False

        # Get the containing book
        books = self.indicdocs.books
        book = books.get(anno_obj['bpath'])
        if not book:
            return False

        page = book['pages'][anno_obj['pgidx']]
        imgpath = join(repodir(), join(anno_obj['bpath'], page['fname']))
        print "Image path = ", imgpath
        page_img = DocImage(imgpath)

        known_segments = DisjointSegments()
        srch_segments = []
        for a in anno_obj['anno']:
            a = ImgSegment(a)
            if a.state == 'system_inferred':
                known_segments.insert(a)
                continue
            a['score'] = float(1.0) # Set the max score for user-identified segments
            # Prevent image matcher from changing user-identified segments
            known_segments.insert(a)
            srch_segments.append(a)

        cfg = serverconfig()
        thres = cfg['template_match']['threshold']

        print "segments to propagate = " + json.dumps(srch_segments)
        # print "Known segments = " + json.dumps(known_segments.segments)
        # For each user-supplied annotation,
        for a in srch_segments:
            # Search for similar image segments within page
            # make sure they are spatially disjoint
            matches = page_img.find_recurrence(a, thres, known_segments)
            #print "Matches = " + json.dumps(matches)
            for r in matches:
                # and propagate its text to them
                r['state'] = 'system_inferred'
                r['text'] = a.text

        known_segments.segments.sort()
        #for r in known_segments.segments:
        #   print str(r)
        #print(known_segments.segments)
        #new_anno = sorted(DotDict(new_anno), key=attrgetter('x', 'y', 'w', 'h'))
        # Save the updated annotations
        self.update(anno_id, { 'anno' : known_segments.segments })
        return True

class Sections:
    def __init__(self, indicdocs):
        self.indicdocs = indicdocs
        self.sections = indicdocs.db['sections']

    def get(self, sec_id):
        res = self.sections.find_one({'_id' : ObjectId(sec_id)})
        res['_id'] = str(res['_id'])
        return res

    def insert(self, sec):
        result = self.sections.insert_one(sec)
        return str(result.inserted_id)

    def update(self, sec_id, section):
        result = self.sections.update({'_id' : ObjectId(sec_id)}, section)
        return result['n'] > 0

class Users:
    def __init__(self, indicdocs):
        self.indicdocs = indicdocs
        self.users = indicdocs.db['users']

    def get(self, user_id):
        res = self.users.find_one({'_id' : ObjectId(user_id)})
        res['_id'] = str(res['_id'])
        return res

    def getBySocialId(self, social_id):
        res = self.users.find_one({'social_id' : social_id})
        if res is not None : res['_id'] = str(res['_id'])
        return res

    def insert(self, user_data):
        result = self.users.insert_one(user_data)
        result = self.get(result.inserted_id)
        result['_id'] = str(result['_id'])
        return result

    def update(self, user_id, user_data):
        result = self.users.update({'_id' : ObjectId(user_id)}, user_data)
        return result['n'] > 0

#class Users:
#    def __init__(docdb):
#        self.users = docdb['users']

class IndicDocs:
    def __init__(self, dbname):
        self.dbname = dbname
        self.initialize()
#        if not database.write_concern.acknowledged:
#            raise ConfigurationError('database must use '
#                                     'acknowledged write_concern')

    def initialize(self):
        try:
            self.client = MongoClient()
            self.db = self.client[self.dbname]
            if not isinstance(self.db, Database):
                raise TypeError("database must be an instance of Database")
            self.books = Books(self)
            self.annotations = Annotations(self)
            self.sections = Sections(self)
            self.users = Users(self)
        except Exception as e:
            print("Error initializing MongoDB database; aborting.", e)
            sys.exit(1)

    def reset(self):
        print "Clearing IndicDocs database"
        self.client.drop_database(self.dbname)
        self.initialize()

#    def exists(self, document_or_id=None, **kwargs):
#        return self.__fs.exists(document_or_id, **kwargs)
#
#    def put(self, data, **kwargs):
#        return self.__fs.put(data, **kwargs)
#
#    def get(self, file_id):
#        return self.__fs.get(file_id)
#
#    def get_last_version(self, filename=None, **kwargs):
#        return self.__fs.get_last_version(filename, **kwargs)
#
#    def list(self):
#        return self.__fs.list()
#
#    def insert_literals(self, file_id, document):
#        record = {'files_id':file_id, "data":document}
#        self.__literals.update({'files_id':file_id}, record, upsert = True)
##        result = self.__literals.insert(record)
#        return self.__literals.find({'files_id':file_id})
#
#    def find_literals(self, file_id):
#        return self.__literals.find({'files_id':file_id})

Mydocs = None
def initdb(dbname, reset=False):
    global Mydocs
    Mydocs = IndicDocs(dbname)
    if reset:
        Mydocs.reset()

def getdb():
    return Mydocs

def main(args):
    setworkdir(workdir())
    initworkdir(False)
    setwlocaldir(DATADIR_BOOKS)
    initdb(INDICDOC_DBNAME, False)

    anno_id = args[0]
    getdb().annotations.propagate(anno_id)

    # Get the annotations from anno_id
    anno_obj = getdb().annotations.get(anno_id)
    if not anno_obj:
        return False

    # Get the containing book
    book = getdb().books.get(anno_obj['bpath'])
    if not book:
        return False

    page = book['pages'][anno_obj['pgidx']]
    imgpath = join(repodir(), join(anno_obj['bpath'], page['fname']))
    img = DocImage(imgpath)

    #print json.dumps(matches)
    rects = anno_obj['anno']
    seeds = [r for r in rects if r['state'] != 'system_inferred']
    img.annotate(rects)
    img.annotate(seeds, (0,255,0))
    cv2.namedWindow('Annotated image', cv2.WINDOW_NORMAL)
    cv2.imshow('Annotated image', img.img_rgb)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
