from flask import Flask, request, redirect, url_for, make_response, abort
from flask import render_template
from werkzeug import secure_filename

from pymongo import MongoClient
from pymongo.database import Database
from config import *
from pprint import pprint

from bson.objectid import ObjectId
import json
from docimage import *
from operator import itemgetter, attrgetter, methodcaller

#from gridfs import GridFS
#from gridfs.errors import NoFile

class DotDict(dict):
    def __getattr__(self, name):
        return self[name]

class Books:
    def __init__(self, indicdocs):
        print "Initializing books collection ..."
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
        page = book.find({"pages.fname", name})
        return page

    def get(self, path):
        book = self.books.find_one({'path' : path})
        book['_id'] = str(book['_id'])
        return book

    def importOne(self, book):
        pgidx = 0
        bpath = book['path']
        for page in book['pages']:
            try:
                anno_id = self.indicdocs.annotations.insert( \
                    { 'bpath' : bpath, 'pgidx' : pgidx, \
                        'anno' : [] })
                sec_id = self.indicdocs.sections.insert( \
                    { 'bpath' : bpath, 'pgidx' : pgidx, \
                        'sections' : [] })
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
                    self.importOne(book)
                    nbooks = nbooks + 1
            except Exception as e:
                print "Skipped book " + f + ". Error:", e
        return nbooks

class Segment:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    def __repr__(self):
        return repr((self.x, self.y, self.w, self.h))

class Annotations:
    def __init__(self, indicdocs):
        self.indicdocs = indicdocs
        self.annotations = indicdocs.db['annotations']
    def get(self, anno_id):
        res = self.annotations.find_one({'_id' : ObjectId(anno_id)})
        res['_id'] = str(res['_id'])
        return res

    def insert(self, anno):
        result = self.annotations.insert_one(anno)
        return str(result.inserted_id)
    def update(self, anno_id, anno):
        #pprint(anno)
        result = self.annotations.update({'_id' : ObjectId(anno_id)}, { "$set": anno })
        isSuccess = (result['n'] > 0)
        return isSuccess

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

        page_img = DocImage(imgpath)

        new_anno = []
        new_anno.extend(anno_obj['anno'])

        # Don't auto-parse user-identified segments
        excl_segments = DisjointSegments()
        for a in anno_obj['anno']:
            a = DotDict(a)
            if a.state != 'system_inferred':
                excl_segments.insert(a)

        # For each user-supplied annotation,
        for a in anno_obj['anno']:
            a = DotDict(a)
            if a.state == 'system_inferred':
                continue
            # Search for similar image segments within page
            matches = page_img.find_recurrence(a, 0.6, excl_segments)
            #print "Matches = " + json.dumps(matches)
            for r in matches:
                # and propagate its text to them
                r['state'] = 'system_inferred'
                r['text'] = a.text
            new_anno.extend(matches)
        #print json.dumps(new_anno)
        #new_anno = sorted(DotDict(new_anno), key=attrgetter('x', 'y', 'w', 'h'))

        # Save the updated annotations
        self.update(anno_id, { 'anno' : new_anno })
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
    def __init__(docdb):
        self.users = docdb['users']

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
    Mydocs.reset()

def getdb():
    return Mydocs
