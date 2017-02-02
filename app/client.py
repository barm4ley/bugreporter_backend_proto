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
status_url = 'http://localhost:8080/status'
# url = 'http://ubuntu-srv-16.westeurope.cloudapp.azure.com/uploads'


def make_content_range_str(start, length, total):
    return 'bytes %(start)d-%(end)d/%(total)d' % \
        {'start': start, 'end': start + length, 'total': total}


def send_meta(filename, url):
    checksum = calculate_file_checksum(filename)

    data = {'filename': filename,
            'checksum': checksum,
            'metadata': {
                'version': '5.5.1f1_88d00a7498cd',
                'description': 'i%20can%27t%20start%20my%20untiy%0A%0A1.%20What%20happened%0A%0A2.%20How%20we%20can%20reproduce%20it%20using%20the%20example%20you%20attached%0A%0A%0ALicense%20type%3A%20Free',
                'bug_type_id': '4',
                'customer_email': 'jiacitan96@gmail.com',
                'title': 'i%20can%27t%20start%20my%20untiy',
                'computer': 'Intel%28R%29%20Core%28TM%29%20i7-4510U%20CPU%20%40%202.00GHz%3B%20NVIDIA%20GeForce%20840M%20%20%20%20%20%20%20%3B%20Windows%2010%20%20%2810.0.0%29%2064bit',
                'timestamp': '2017-02-02 13:10:22',
                'bug_reproducibility': 'Always'
                }
            }

    headers = {'X-Upload-FileName': filename, 'X-FILE-CHECKSUM': checksum}
    resp = requests.post(url, json=data, headers=headers)
    logger.debug(resp.json())
    logger.debug(resp.headers)
    return resp.json()


def send_file(filename, url, chunk_size, start_chunk_num, end_chunk_num=None):
    contents = mmap_file(filename)
    chunks_num = calc_chunks_num(filename, chunk_size)
    file_size = os.path.getsize(filename)

    end_chunk = end_chunk_num if end_chunk_num else chunks_num

    for chunk in range(start_chunk_num, chunks_num):
        chunk_data = get_chunk(contents, chunk, chunk_size)
        chunk_checksum = calculate_checksum(chunk_data)

        start = chunk * chunk_size

        range_str = make_content_range_str(start, len(chunk_data), file_size)
        headers = {'Content-Range': range_str,
                   'X-CHUNK-CHECKSUM': chunk_checksum}

        resp = requests.put(url, data=chunk_data, headers=headers)
        if resp.status_code != 308:
            break

def get_status(url, sid):
    url = url + '/' + sid
    resp = requests.get(url)

    logger.debug(resp.json())
    logger.debug(resp.headers)

    return resp.json()

def main():
    meta_data = send_meta('test.txt', url)
    sid = meta_data['sid']
    chunk_size = meta_data['chunk_size']

    send_file('test.txt', url + '/' + sid, chunk_size, 0)

    get_status(status_url, sid)

if __name__ == '__main__':
    main()
