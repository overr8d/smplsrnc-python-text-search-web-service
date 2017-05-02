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





