#!/usr/bin/env python3

import os
from flask import Flask, request, redirect, url_for, jsonify
from werkzeug import secure_filename
# from splitcat import make_file_part_name
from splitcat import check_file_consistency, check_consistency
from uuid import uuid4

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNK_SIZE = 4096

UPLOAD_FOLDER = '/tmp/'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

sessions = {}


def allowed_file(filename):
    return True
    # return '.' in filename and \
    #        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/uploads/<sid>', methods=['PUT'])
def upload_file_part(sid):

    logger.debug('uploads/%s' % sid)

    ret_code = 308

    files = request.files

    logger.debug('files: %s' % files)

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

        logger.debug(range_str)

        logger.debug('start_bytes %d' % start_bytes)

        chunk_data = value.stream.read()
        chunk_checksum = request.headers['X-CHUNK-CHECKSUM']

        if not check_consistency(chunk_data, chunk_checksum):
            logger.error('Chunk transmission error: checksum calculation failed')
            return 'OK', 416

        # append chunk to the file on disk or create new file
        with open(full_name, 'ab') as ofile:
            ofile.seek(start_bytes)
            ofile.write(chunk_data)

        logger.debug('File size: %d' % os.path.getsize(full_name))

        if os.path.getsize(full_name) == total_bytes:
            if check_file_consistency(full_name, sessions[sid]['checksum']):
                logger.debug('File consistent')
                ret_code = 308
            else:
                logger.debug('File is broken')
                ret_code = 201
            return 'OK', ret_code
    else:
        logger.debug('Invalid request')
        # value.save(full_name)

    return 'OK', 308


@app.route("/uploads", methods=['POST'])
def upload():

    logger.debug('/uploads')

    data = request.get_json()

    if 'sid' in data:
        sid = data['sid']
    else:
        sid = str(uuid4())

    if sid in sessions:
        return jsonify({'sid': sid,
                        'status': 'failure',
                        'description': 'session already exists'})

    sessions[sid] = data

    dirname = os.path.join(app.config['UPLOAD_FOLDER'], sid)
    os.mkdir(dirname)

    chunk_size = CHUNK_SIZE  # Maybe should be dynamically calculated

    resp = jsonify({'sid': sid,
                    'chunk_size': chunk_size,
                    'status': 'success'})

    resp.headers['X-SID'] = sid
    resp.headers['X-CHUNK-SIZE'] = chunk_size
    return resp


@app.route("/", methods=['GET', 'POST'])
def index():

    logger.debug('index')

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
    app.run(host='0.0.0.0', port=8080, debug=True)
