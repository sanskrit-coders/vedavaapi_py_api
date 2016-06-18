from flask import Flask, request, redirect, url_for, make_response, abort
from flask import render_template
from werkzeug import secure_filename

from pymongo import MongoClient
from pymongo.database import Database

from bson.objectid import ObjectId
import json

from gridfs import GridFS
from gridfs.errors import NoFile

class IndicDocDB:
    def __init__(self, dbname):
        try:
            client = MongoClient()
            self.db = client[dbname]
            if not isinstance(self.db, Database):
                raise TypeError("database must be an instance of Database")
        except Exception as e:
            print("Error initializing MongoDB database", e)
            sys.exit(1)


#        if not database.write_concern.acknowledged:
#            raise ConfigurationError('database must use '
#                                     'acknowledged write_concern')

        #self.users = self.db['users']
        #self.books = self.db['books']
        #self.annotations = self.db['annotations']

        #self.__database = database
        #self.__literals = database[collection]
        #self.__fs = GridFS(database) 

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

class Books:
    def __init__(self, docdb):
        self.books = docdb['books']

    def insert(self, book):
        self.books.update({'path' : book.path}, book, upsert=True)
        return self.books.find({'path': book.path}).count()

    def list(self, pattern=None):
        cursor = self.books.find()
        matches = [b for b in cursor if not pattern or re.search(pattern, b.name)]
        return matches

    def getPage(self, book, idx):
        return self.book.pages[idx]

    def get(self, path):
        return self.books.find_one({'path' : path})

    def importAll(pattern = None):
        cmd = "find "+repodir()+" \( \( -path '*/.??*' \) -prune \) , \( -path '*.json' \) -follow -print; true"
        try: 
            results = mycheck_output(cmd)
        except Exception as e:
            print "Error in find: ", e
            return 0

        nbooks = 0
        for f in results.split("\n"):
            if not f:
                continue
            bpath = f.replace(repodir() + "/", "")
            if pattern and not re.search(pattern, bpath, re.IGNORECASE):
                continue
            winfo = {}
            try: 
                with open(f) as fhandle:
                    book = json.load(fhandle)
                    book['path'] = bpath
                    self.insert(book)
                    nbooks = nbooks + 1
            except Exception as e:
                print "Skipped book " + f + ". Error:", e
        return nbooks

class Users:
    def __init__(docdb):
        self.users = docdb['users']


Mydb = None
Mybooks = None
Myusers = None
def initdb(dbname):
    Mydb = IndicDocDB(dbname)
    Mybooks = Books(Mydb)

def resetdb(dbname):
    MongoClient().drop_database(dbname)
    initdb(dbname)
