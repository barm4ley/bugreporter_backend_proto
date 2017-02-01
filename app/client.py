#!/usr/bin/env python3

import requests
from splitcat import mmap_file, calc_chunks_num, calculate_checksum, calculate_file_checksum, get_chunk
import os

import logging


try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Disable requests verbosity
# logging.getLogger('requests').setLevel(logging.CRITICAL)


url = 'http://localhost:8080/uploads'
# url = 'http://ubuntu-srv-16.westeurope.cloudapp.azure.com/uploads'


def make_content_range_str(start, length, total):
    return 'bytes %(start)d-%(end)d/%(total)d' % \
        {'start': start, 'end': start + length, 'total': total}


def send_meta(filename, url):
    checksum = calculate_file_checksum(filename)

    # data = {'filename': filename, 'checksum': checksum, 'sid': sid}
    data = {'filename': filename, 'checksum': checksum}
    headers = {'X-Upload-FileName': filename}
    resp = requests.post(url, json=data, headers=headers)
    logger.debug(resp.json())
    logger.debug(resp.headers)
    return resp.json()


def send_file(filename, url, chunk_size):
    contents = mmap_file(filename)
    chunks_num = calc_chunks_num(filename, chunk_size)
    file_size = os.path.getsize(filename)

    for chunk in range(chunks_num):
        chunk_data = get_chunk(contents, chunk, chunk_size)
        chunk_checksum = calculate_checksum(chunk_data)

        start = chunk * chunk_size

        range_str = make_content_range_str(start, len(chunk_data), file_size)
        headers = {'Content-Range': range_str,
                   'X-CHUNK-CHECKSUM': chunk_checksum}

        # files = {filename: chunk_data}

        # resp = requests.put(url, files=files, headers=headers)
        resp = requests.put(url, data=chunk_data, headers=headers)
        if resp.status_code != 308:
            break


def main():
    meta_data = send_meta('test.txt', url)
    sid = meta_data['sid']
    chunk_size = meta_data['chunk_size']

    send_file('test.txt', url + '/' + sid, chunk_size)


if __name__ == '__main__':
    main()
