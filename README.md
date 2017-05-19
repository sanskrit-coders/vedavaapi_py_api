TOC generated using [this](https://tableofcontents.herokuapp.com/) (needs to be manually updated).
- [Introduction](#introduction)
- [Usage](#usage)
  - [Setup](#setup)
  - [Running](#running)
- [Development](#development)
  - [Understanding the code](#understanding-the-code)
   - [Run code](#run-code)
    - [common package](#common-package)
   - [Textract](#textract)
    - [Backend](#backend)
  - [Guidelines](#guidelines)

# Introduction
Python based Web API's for the <vedavaapi.org> project.  

# Usage
## Setup
* We're currently using Python 2.7.
  * The installation procedure for the cv2 module with Python3.5 is fairly elaborate as of 20170423.
* Install various necessary python modules.
  * install.pl might help.
* Grant the account running run.py authority to write in /opt/scan2text/.
  * sudo mkdir /opt/scan2text/; sudo chmod a+rwx /opt/scan2text
  * ln -s ~/vedavaapi_py_api/textract/example-repo/books /opt/scan2text/data/


## Running
* Launch server: run.py

### Diagnostics
* List routes: /sitemap on your browser.

## Accessing API docs:
* Generally, just try the /docs/ path under the appropriate module. Example: http://localhost:9000/textract/docs/ .

# Development
## Understanding the code
* Can generate call graphs:
  * pyan.py --dot -c -e run.py |dot -Tpng > call_graphs/run.png

### Run code
* [run.py]() :
  * starts the webservice
  * sets up actions to be taken when various URL-s are accessed.

#### common package
* [flask_helper.py]()
  * Sets up the flask app.
  * Defines some basic handlers.
* [config.py]() contains various helper methods


### Textract
#### Intro
This is a web-based tool to rapidly decode scanned Indic document images into searchable text. It enables users to identify and
 annotate characters in scanned document images and auto-identifies similar characters.
 Allows users to correct and uses them in subsequent text recognition.


#### Root module
* [__init__.py]():
  * creates local temporary and data directories
* [api_v1.py]():
  * Handles calls to /textract/*


#### Backend
* [data_containers.py]() defines
  * various objects such as BookPortion, Annotation, SandhiAnnotation.
  * json helper methods to (de)serialize them to json while writing to the database.
* [db.py and collections.py]() :
  * Sets up database (an IndicDocs object) with initdb() and getdb()
  * Declares various other pymongo db collection containers, with methods for create /update / insert operations:
    * Books
    * Annotations
    * Sections
    * Users

## Guidelines
* Don't write ugly code.
  * Remember that your code will be read many more times than it will be written. Please take care.
  * Use meaningful identifier names (no naming global functions "myerror").
  * Follow the appropriate language-specific conventions for identifier naming and code formatting.
* Don't reinvent the wheel (Eg. Don't write your own logging module). Reuse and share code where possible.
* Separate client and server logic.
  * Avoid setting variables using flask templates. The js code should get data by making AJAX calls to the server. 
  * In fact, one should be able to write (totally separate) pure html/ js code which will communicate with the server only using AJAX calls.
* Respect the code structure.
  * JS, python, html template code for different apps are in different directories.
* While designing REST API:
  * Read up and follow the best practices. When in doubt, discuss.
  * Currently we use flask restplus, and set the API docs to appear under the /doc/ path as described in the usage section.
  