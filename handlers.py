import os
import os.path
import thread
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
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
    filename : str
        
"""
def delete_from_index(filename):
    ix.delete_by_term("path", unicode(filename))
    os.unlink(os.path.join(UPLOAD_FOLDER, str(filename)))

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
    Parses the request param "q" and passes it to a thread for searching task
    Searches query param/s through the index schema
    Returns corresponding filename/s in result.html template

    Returns
    -------
    template: .../templates/result.html
        
"""          
def search_handler():
    query = request.args.get('q')
    with ix.searcher() as searcher:
        _query = QueryParser("content", ix.schema).parse(unicode(query))
        results = searcher.search(_query)
        return render_template('result.html', results=results)



    





