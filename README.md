# SMPLSRNC - Programming Assignment: Python Text Search Web Service

Text search web service is implemented using the files outlined below:

- Server (`server.py`) defines the routers defined for a given task, and invokes corresponding handler functions from 'handlers.py'.
- Server handlers (`handlers.py`) holds the handler functions that help indexing, deleting, retrieving files and searching the parameters passed by URLS.
- Result template (`/templates/result.html`) displays search results in a rendered template. 
- Python packages list (`requirements.txt`) stores the name of packages that the application relies on in order to perform properly. It is handy, when developing in isolated environments like 'virtualenv' and installing dependencies in a bulky fashion by passing it as a parameter to 'pip'.
- Text folder (`/text`) It is for test purposes only. Holds some books in 'txt' format that a user can upload to web service.

### Requirements:

- [x] The service should hold all data in memory.
- [x] POST /document/XXX Saves a text document with ID XXX.
- [x] GET /document/XXX Returns the text document with ID XXX.
- [x] Documents are just text. (no fields to parse)
- [x] GET /search?q={word} Returns the list of IDs from documents with content that match the given keyword. (single word search)
- [x] DELETE /document/XXX Deletes document with ID XXX.

### Extra:

- [x] GET /search?q={word1 word2 ... wordN} Returns the list of document IDs that match all the keywords.

## How it works 

In this application, the test taker is asked to create a text search web service that enables clients to upload,delete and retrieve text files and search them by keyword/s. To do so, a popular, lightweight web framework [Flask](http://flask.pocoo.org/) has been incorporated to handle GET, POST, DELETE requests. Also,  [Whoosh](https://pypi.python.org/pypi/Whoosh/), a full text indexing and search library has been included to meet the document related requirements given above. 

(`server.py`)

```python
from flask import Flask, request
from handlers import * 

app = Flask(__name__)
 
# Handles the files posted to URL: ..../document       
@app.route("/document", methods=['POST'])
def upload():
    if request.method == 'POST':
        return upload_handler(request)
            
# Displays or deletes the file specified in URL: ...../document/<path:filename>   
@app.route("/document/<path:filename>", methods = ["GET", "DELETE"])
def get_or_delete(filename):
	if request.method == "GET":
	   return get_handler(filename)
	elif request.method == "DELETE":
            return delete_handler(filename)   

# Returnes a list of document names that includes the given keyword/s ==> {word1} / {word1 word2 word3 ... wordN}           
@app.route("/search")
def search():
    return search_handler()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

```
Above script works as follows:

* Captures POST requests sent to `localhost:5000/document` and returns a result from `upload_handler()`.
* Captures GET or DELETE requests sent to `localhost:5000/document`, fetches the specified filename in the URL and returns a result from either `get_handler` or `delete_handler()`.
* Captures GET requests sent to `localhost:5000/search`and returns a result from `search_handler()`.  
* `app.run()` is run setting `threaded=True` which allows multiple clients to communicate with server concurrently, as long as the underlying OS's thread limits are not exercised. 

Handler functions are implemented as follows:

(`handlers.py`)

```python
import os
import os.path
import thread
from whoosh.index import create_in
from whoosh.fields import *
from whoosh import qparser
from werkzeug import secure_filename
from flask import request, redirect, send_from_directory, render_template


""""""""""""""" Initial Setup """""""""""""""""""""
ALLOWED_EXTENSIONS = set(['txt','text'])
UPLOAD_FOLDER = 'uploaded_files'
INDEX_FOLDER  = 'index'

# Creates a folder for storing uploaded documents
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
# Creates a folder for storing index schemas
if not os.path.exists(INDEX_FOLDER):
    os.mkdir(INDEX_FOLDER)

# Creates a schema to be used for indexing and searching
schema = Schema(path=TEXT(stored=True), content=TEXT)
ix = create_in("index", schema)

""""""""""""""""""""""""""""""""""""""""""""""""
```

* To initialize, the script sets some global variables, `ALLOWED_EXTENSIONS` to specify file extensions allowed, `UPLOAD_FOLDER` to specify a folder name that will hold uploaded files, `INDEX_FOLDER` to specify a folder name that will hold indexing file to created by Whoosh. 
* If specified folders are not present in the application directory, creates them accordingly. 
* In order to hold indexed data in memory, Schema object is invoked from Whoosh that stores the path and the content of the given file. The schema object is created with a name `index`.

```python
"""
    Returns a file specified in filename

    Parameters
    ----------
    filename : str

    Returns
    -------
    .text or .txt file
        
"""    
def get_handler(filename):
    return send_from_directory(UPLOAD_FOLDER, str(filename))

"""
    Passes the deleting task to a thread

    Parameters
    ----------
    filename : str

    Returns
    -------
    str: "Success"
        
"""               
def delete_handler(filename):
    try:
        thread.start_new_thread(delete_from_index, (filename,))   
    except:
        print ("Error: unable to start a thread!")
    return "Success!"

"""
    Deletes a given file from UPLOAD_FOLDER, and clears out its indexing in the index schema

    Parameters
    ----------
    filename : str
        
"""

def delete_from_index(filename):
    ix.delete_by_term("path", unicode(filename))
    os.unlink(os.path.join(UPLOAD_FOLDER, str(filename)))
    
 ```
 
* `get_handler()` is invoked when a client sends a GET request to server, passing a `filename` as a URL parameter. Returns a specified file by calling `send_from_directory` function from `Flask`.
* `delete_handler()` is invoked when the client sends a DELETE request to server, passing a `filename` as a URL parameter. Passes the deletion task to a thread, allowing the main thread to keep on serving the client. 
* `delete_from_index()` is called by the thread just spawned. Deletes the file from a folder and wipes it out from index schema. In the meantime, `Whoosh` keeps serving the old indexing data to the clients submitting requests until the deletion completes. 

```python
"""
    Checks if the file extension conforms to pre-defined file formats: ALLOWED_EXTENSION

    Parameters
    ----------
    filename : str

    Returns
    -------
    str
        
"""
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

"""
    Reads a file into list and indexs it into indexing schema
    Writes the document into index schema in a given format: {path=filename, content=content} 

    Parameters
    ----------
    filename : str
    
"""
def write_to_index(filename):
   
    lines = []
    with open('{}{}{}'.format(UPLOAD_FOLDER,'/', filename)) as file:
        for line in file:
            line = line.strip() 
            lines.append(line)
        writer = ix.writer()
        writer.add_document(path=unicode(filename),
            content= unicode(lines))
        writer.commit()

"""
    Deletes a given file from UPLOAD_FOLDER, and clears out its indexing in the index schema

    Parameters
    ----------
    request : obj
        
"""         
def upload_handler(request):
    # check if the post request has the file part
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    # check if filename is empty
    if file.filename == '':
        return redirect(request.url)
    if allowed_file(file.filename):
        # returns an ASCII only string for maximum portability
        filename = secure_filename(file.filename)
        file.save(os.path.join('{}{}'.format(UPLOAD_FOLDER,'/'), filename))
        #passes the indexing task to a tread
        try:
            thread.start_new_thread(write_to_index, (filename,)) 
        except:
            print ("Error: unable to start a thread")
        return "Success!"
    else: 
        return "File format not allowed!"
```

* `allowed_file()` checks if the filename passed into the function conforms to `ALLOWED_EXTENSIONS`.
* `upload_handler()` takes request object as a parameter from the URL itself, checks if there is any file attached, if so saves the file to a folder, and spawns a thread that invokes  `write_to_index()`. It is worth mentioning that, in order to keep the main thread fully responsive, threading is implemented.
* `write_to_index()` parses the lines from a file, appends them to  `lines` list and passes it indexing schema.

```python
"""
    Parses the request param "q"
    Searches query param/s through the index schema
    Returns corresponding filename/s in result.html template

    Returns
    -------
    template: .../templates/result.html
        
"""          
def search_handler():
    query = request.args.get('q')
    with ix.searcher() as searcher:
        # Changes the parser to use "OR" instead: param1 OR param2 OR param3...
        parser = qparser.QueryParser("content", ix.schema,
                                 group=qparser.OrGroup)
        _query = parser.parse(unicode(query))
        results = searcher.search(_query)
        return render_template('result.html', results=results)
```

* `search_handler()` parses a `q` parameter from a request object, search it through index schema and returns the result in the rendered template. One thing to note here, QueryParser accepts multiple parameters, allowing the developer to implement the same function for both single and multiple keyword/s cases. `group=qparser.OrGroup` is specified to allow the parameters to be connected by OR.
* In this section, performance issues pop up in minds under heavy search requests and many file uploads, but per the emprical tests conducted, `Whoosh` library performed very well, thus the idea of implementing another solution was utterly discarded.

## How to launch the app

* Run `python server.py` to fire up the server.
* Run [Postman](https://www.getpostman.com/) or another solution to send custom requests to API/web service.
* Send POST request to `localhost:5000/document` as shown below to upload a file to web service.

<img width="680" alt="post_document" src="https://cloud.githubusercontent.com/assets/18366839/25673901/ae0a08f8-3041-11e7-9ff7-d97f6b953671.png">

* Send GET request to `localhost:5000/document/filename` by replacing the `filename` parameter with a specific file name to retrieve the corresponding file. 

<img width="680" alt="get_document" src="https://cloud.githubusercontent.com/assets/18366839/25673899/ae036afc-3041-11e7-8186-7dbc47ddc69e.png">

* Send DELETE request to `localhost:5000/document/filename` by replacing the `filename` parameter with a specific file name to delete the corresponding file. 

<img width="680" alt="delete_document" src="https://cloud.githubusercontent.com/assets/18366839/25673898/adfe8672-3041-11e7-92f3-e2a4a407be71.png">

* Send GET request to `localhost:5000/search?q={word1}` by replacing the `word1` parameter with a keyword or keywords to retrieve the list of files containing the parameter/s. 

<img width="680" alt="get_search" src="https://cloud.githubusercontent.com/assets/18366839/25673900/ae0762c4-3041-11e7-922d-b664cedef3c9.png">

## Prerequisites

* Python 2.7
* Mozilla Firefox 42 or Google Chrome 46 or later
* Postman Version 4.10.7

