#!/usr/bin/env python3

import os
from flask import Flask, request, redirect, url_for, jsonify
from werkzeug import secure_filename
# from splitcat import make_file_part_name
from splitcat import check_file_consistency, check_consistency, byte_offset_to_chunk_num
from uuid import uuid4
import shutil

from session import Session, SessionsRepo, UPLOAD_STATUS_FINISHED
from bugreporter_helper import make_metadata_file, make_report_dir

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


CHUNK_SIZE = 4096
chunk_size = CHUNK_SIZE

UPLOAD_DIR = '/tmp/'
PROCESSOR_DIR = '/tmp/bugz/'

ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_DIR'] = UPLOAD_DIR
app.config['PROCESSOR_DIR'] = PROCESSOR_DIR

sessions_repo = SessionsRepo()


def allowed_file(filename):
    return True
    # return '.' in filename and \
    #        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route("/uploads", methods=['POST'])
def upload_init():

    logger.debug('/uploads')

    sid = str(uuid4())

    session = Session(sid)

    sessions_repo.add(session)

    data = request.get_json()

    if 'X-Upload-Content-Length' in request.headers:
        logger.debug('X-Upload-Content-Length: %s' % request.headers['X-Upload-Content-Length'])

    session.filename = secure_filename(data['filename'])
    session.checksum = data['checksum']

    session.upload_status = -1

    logger.debug(session.filename)
    logger.debug(session.checksum)

    dirname = os.path.join(app.config['UPLOAD_DIR'], session.sid)
    os.mkdir(dirname)

    make_metadata_file(data['metadata'], dirname)

    resp = jsonify({'sid': session.sid,
                    'chunk_size': chunk_size,
                    'status': 'success'})

    resp.headers['X-SID'] = sid
    resp.headers['X-CHUNK-SIZE'] = chunk_size
    resp.headers['Location'] = url_for('upload_file_part', sid=session.sid)
    return resp


@app.route('/uploads/<sid>', methods=['PUT'])
def upload_file_part(sid):

    session = sessions_repo.get(sid)

    ret_code = 308

    # logger.debug(request.data)

    filename = session.filename
    temp_report_dir = os.path.join(app.config['UPLOAD_DIR'], sid)
    full_name = os.path.join(temp_report_dir, filename)

    if 'Content-Range' in request.headers:
        # extract starting byte from Content-Range header string
        range_str = request.headers['Content-Range']
        start_bytes = int(range_str.split(' ')[1].split('-')[0])
        total_bytes = int(range_str.split(' ')[1].split('/')[1])

        chunk_data = request.data
        chunk_checksum = request.headers['X-CHUNK-CHECKSUM']

        if not check_consistency(chunk_data, chunk_checksum):
            logger.error('Chunk transmission error: checksum calculation failed')
            return 'OK', 416

        # append chunk to the file on disk or create new file
        with open(full_name, 'ab') as ofile:
            ofile.seek(start_bytes)
            ofile.write(chunk_data)

        session.last_chunk = byte_offset_to_chunk_num(start_bytes, chunk_size)

        if os.path.getsize(full_name) == total_bytes:
            logger.debug('File size: %d' % os.path.getsize(full_name))

            session.status = UPLOAD_STATUS_FINISHED

            if check_file_consistency(full_name, session.checksum):
                logger.debug('File consistent')

                report_dir = make_report_dir(app.config['PROCESSOR_DIR'])

                shutil.move(os.path.join(temp_report_dir, filename), os.path.join(report_dir, filename))
                shutil.move(os.path.join(temp_report_dir, 'metadata.pl'), os.path.join(report_dir, 'metadata.pl'))
                os.removedirs(temp_report_dir)

                ret_code = 201
            else:
                logger.debug('File is broken')
                ret_code = 416
            return 'OK', ret_code
            # return 'OK', 201
    else:
        logger.debug('Invalid request')
        # value.save(full_name)

    return 'OK', 308


@app.route('/status/<sid>', methods=['GET'])
def upload_status(sid):

    session = sessions_repo.get(sid)

    resp = jsonify({'sid': sid,
                    'chunk_size': chunk_size,
                    'last_chunk': session.last_chunk,
                    'status': session.status})

    resp.headers['Location'] = url_for('upload_file_part', sid=session.sid)

    if session.status == UPLOAD_STATUS_FINISHED:
        sessions_repo.delete(session.sid)

    return resp


@app.route("/", methods=['GET', 'POST'])
def index():

    logger.debug('index')

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_DIR'], filename))
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
    """ % "<br>".join(os.listdir(app.config['UPLOAD_DIR'],))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
