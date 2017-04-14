# Introduction
## scan2text
Community-based Indic Manuscript Decoder

This is a web-based tool to rapidly decode scanned Indic document images into searchable text. It enables users to identify and
annotate characters in scanned document images and auto-identifies similar characters.
Allows users to correct and uses them in subsequent text recognition.

# Usage
## Setup
* Install various necessary python modules.
  * install.pl might help.
* Grant the account running run.py authority to write in /opt/scan2text/.
  * sudo mkdir /opt/scan2text/; sudo chmod a+rwx /opt/scan2text

## Running
* Launch server: run.py

# Development
## Understanding the code
* [run.py]() :
  * starts the webservice
  * creates local temporary and data directories
  * sets up actions to be taken when various URL-s are accessed.
    * Some of this is redirected to books_api in [books.py]() .
* [indicdocs.py]() :
  * Sets up database (an IndicDocs object) with initdb() and getdb()
  * Declares various other pymongo db collection containers, with methods for create /update / insert operations:
    * Books
    * Annotations
    * Sections
    * Users
* [config.py]() contains various helper methods
  * most of which are for setup and file operations.
  * Some salient ones pertaining to formatting json responses are:
    * gen_response()
    * myerror()
    * myresult()
  * Logging functions which need to be replaced.
* Can generate call graphs:
  * pyan.py --dot -c -e run.py |dot -Tpng > call_graphs/run.png
