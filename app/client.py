#!/usr/bin/env python3

import requests
from splitcat import mmap_file, calc_chunks_num, calculate_file_checksum, get_chunk
# from uuid import uuid4
import os


CHUNK_SIZE = 4096

url = 'http://localhost:8080/uploads'
# url = 'http://ubuntu-srv-16.westeurope.cloudapp.azure.com/uploads'
# sid = str(uuid4())


def make_content_range_str(start, length, total):
    return 'bytes %(start)d-%(end)d/%(total)d' % \
        {'start': start, 'end': start + length, 'total': total}


def send_meta(filename, url):
    checksum = calculate_file_checksum(filename)

    # data = {'filename': filename, 'checksum': checksum, 'sid': sid}
    data = {'filename': filename, 'checksum': checksum}
    resp = requests.post(url, json=data)
    print(resp.json())
    return resp.json()['sid']


def send_file(filename, url):
    contents = mmap_file(filename)
    chunks_num = calc_chunks_num(filename, CHUNK_SIZE)
    file_size = os.path.getsize(filename)

    for chunk in range(chunks_num):
        # time.sleep(1)
        chunk_data = get_chunk(contents, chunk, CHUNK_SIZE)
        start = chunk * CHUNK_SIZE

        range_str = make_content_range_str(start, len(chunk_data), file_size)
        headers = {'Content-Range': range_str}
        files = {filename: chunk_data}

        requests.put(url, files=files, headers=headers)


def main():
    sid = send_meta('test.txt', url)
    send_file('test.txt', url + '/' + sid)


if __name__ == '__main__':
    main()
