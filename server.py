#!/usr/bin/env python3

import os
from flask import Flask, request, redirect, url_for, jsonify
from werkzeug import secure_filename
from splitcat import make_file_part_name, check_file_consistency


UPLOAD_FOLDER = '/tmp/'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

sessions = {}

def allowed_file(filename):
    return True
    # return '.' in filename and \
    #        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


#@app.route('/uploads/<sid>', methods=['PUT'])
#def upload_file_part():
    #files = request.files

    ## assume that only one file passed
    #key = list(files.keys())[0]
    #value = files[key]
    ## filename = secure_filename(value.filename)
    #filename = sessions[sid]['filename']

    #if 'ChunkNo' in request.headers:
        #chunk_no = int(request.headers['ChunkNo'])
    #else:
        #return '', 404

    #full_name = os.path.join(app.config['UPLOAD_FOLDER'],
                             #make_file_part_name(filename, chunk_no))

    #if 'Content-Range' in request.headers:
        ## extract starting byte from Content-Range header string
        ## range_str = request.headers['Content-Range']
        ## start_bytes = int(range_str.split(' ')[1].split('-')[0])

        ## append chunk to the file on disk or create new file
        #with open(full_name, 'ab') as ofile:
            ## ofile.seek(start_bytes)
            #ofile.write(value.stream.read())
    #else:
        #value.save(full_name)


@app.route('/uploads/<sid>', methods=['PUT'])
def upload_file_part(sid):
    files = request.files

    # assume that only one file passed
    key = list(files.keys())[0]
    value = files[key]
    filename = secure_filename(value.filename)
    full_name = os.path.join(app.config['UPLOAD_FOLDER'], sid, filename)

    if 'Content-Range' in request.headers:
        # extract starting byte from Content-Range header string
        range_str = request.headers['Content-Range']
        start_bytes = int(range_str.split(' ')[1].split('-')[0])
        total_bytes = int(range_str.split(' ')[1].split('/')[1])
        print(range_str)

        print('start_bytes %d' % start_bytes)

        # append chunk to the file on disk or create new file
        with open(full_name, 'ab') as ofile:
            ofile.seek(start_bytes)
            ofile.write(value.stream.read())

        print('File size: %d' % os.path.getsize(full_name))

        if os.path.getsize(full_name) == total_bytes:
            if check_file_consistency(full_name, sessions[sid]['checksum']):
                print('File consistent')
            else:
                print('File is broken')
    else:
        print('Invalid request')
        # value.save(full_name)

    return 'OK'


@app.route("/uploads", methods=['POST'])
def upload():
    data = request.get_json()

    print(data)
    sid = data['sid']

    if sid in sessions:
        return jsonify({'status': 'failure',
                        'description': 'session already exists'})

    sessions[sid] = data

    dirname = os.path.join(app.config['UPLOAD_FOLDER'], sid)
    os.mkdir(dirname)

    return jsonify({'status': 'success'})





@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index'))
    return """
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    <p>%s</p>
    """ % "<br>".join(os.listdir(app.config['UPLOAD_FOLDER'],))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
