from flask import Flask, request, redirect, url_for, make_response, abort
from flask import render_template
from werkzeug import secure_filename

from pymongo import MongoClient
from pymongo.database import Database
from config import *
from pprint import pprint

from bson.objectid import ObjectId
import json

#from gridfs import GridFS
#from gridfs.errors import NoFile

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
        matches = [b for b in cursor if not pattern or re.search(pattern, b.name)]
        return matches

    def getPageByIdx(self, book, idx):
        return book.pages[idx]

    def getPageByName(self, book, pagename):
        page = book.find({"pages.fname", name})
        return page

    def get(self, path):
        binfo = self.books.find_one({'path' : path})
        binfo['_id'] = str(binfo['_id'])
        return binfo

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
                    pgidx = 0
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
                    nbooks = nbooks + 1
            except Exception as e:
                print "Skipped book " + f + ". Error:", e
        return nbooks

class Annotations:
    def __init__(self, docdb):
        self.annotations = docdb['annotations']
    def get(self, anno_id):
        res = self.annotations.find_one({'_id' : ObjectId(anno_id)})
        res['_id'] = str(res['_id'])
        return res

    def insert(self, anno):
        result = self.annotations.insert_one(anno)
        return str(result.inserted_id)
    def update(self, anno_id, anno):
        pprint(anno)
        result = self.annotations.update({'_id' : ObjectId(anno_id)}, anno)
        isSuccess = (result['n'] > 0)
        return isSuccess

class Sections:
    def __init__(self, docdb):
        self.sections = docdb['sectations']
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
            self.books = Books(self)
            self.annotations = Annotations(self.db)
            self.sections = Sections(self.db)
            if not isinstance(self.db, Database):
                raise TypeError("database must be an instance of Database")
        except Exception as e:
            print("Error initializing MongoDB database", e)
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
