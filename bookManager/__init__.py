from flask import Flask, request, redirect, url_for, make_response, abort
from flask import render_template
from werkzeug import secure_filename

from pymongo import MongoClient
from pymongo.database import Database

from bson.objectid import ObjectId
import json

from gridfs import GridFS
from gridfs.errors import NoFile

class BookManager(object):

    def __init__(self, database, collection="literals"):
        if not isinstance(database, Database):
            raise TypeError("database must be an instance of Database")

#        if not database.write_concern.acknowledged:
#            raise ConfigurationError('database must use '
#                                     'acknowledged write_concern')

        self.__database = database
        self.__literals = database[collection]
        self.__fs = GridFS(database) 

    def exists(self, document_or_id=None, **kwargs):
        return self.__fs.exists(document_or_id, **kwargs) 

    def put(self, data, **kwargs):
        return self.__fs.put(data, **kwargs)

    def get(self, file_id):
        return self.__fs.get(file_id)

    def get_last_version(self, filename=None, **kwargs):
        return self.__fs.get_last_version(filename, **kwargs)

    def list(self):
        return self.__fs.list()

    def insert_literals(self, file_id, document):
        record = {'files_id':file_id, "data":document}
        self.__literals.update({'files_id':file_id}, record, upsert = True)
#        result = self.__literals.insert(record)
        return self.__literals.find({'files_id':file_id})

    def find_literals(self, file_id):
        return self.__literals.find({'files_id':file_id})

