#!/usr/bin/env python3

import mmap
import os
from math import ceil
import logging
import sys
import hashlib

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def calculate_file_checksum(filename):
    return hashlib.md5(open(filename, 'rb').read()).hexdigest()


def check_file_consistency(filename, digest):
    return calculate_file_checksum(filename) == digest


def mmap_file(filename):
    logger.debug('mmaping %s file' % filename)
    with open(filename, 'r+b') as src:
        return mmap.mmap(src.fileno(), 0)


def calc_chunks_num(filename, chunk_len=4096):
    return ceil(os.path.getsize(filename) / chunk_len)


def get_chunk(contents, chunk_number, chunk_len=4096):
    # logger.debug('Extracting chunk %d' % chunk_number)
    start = chunk_number * chunk_len
    end = start + chunk_len
    return contents[start:end]


def make_file_part_name(base_name, chunk_number):
    return base_name + '.%04d' % chunk_number


def generate_file_part(base_name, chunk_contents, chunk_number):
    filename = make_file_part_name(base_name, chunk_number)
    # logging.debug('Writing file %s' % filename)
    with open(filename, 'wb') as f:
        f.write(chunk_contents)


def concat_files(base_name, chunks_number):
    with open(base_name, 'wb') as ofile:
        for index in range(chunks_number):
            with open(make_file_part_name(base_name, index), 'r+b') as part:
                ofile.write(part.read())


def main():
    filename = "test.txt"

    contents = mmap_file(filename)
    checksum = calculate_file_checksum(filename)
    logger.debug('Checksum - %s' % checksum)

    chunks_num = calc_chunks_num(filename)
    logger.debug('Chunks num %d' % chunks_num)

    for chunk in range(chunks_num):
        chunk_base_name = '/tmp/' + filename
        chunk_contents = get_chunk(contents, chunk)
        generate_file_part(chunk_base_name, chunk_contents, chunk)

    concat_files('/tmp/' + filename, chunks_num)

    if check_file_consistency('/tmp/' + filename, checksum):
        logger.debug('Concatenation successfull')


if __name__ == '__main__':
    main()
