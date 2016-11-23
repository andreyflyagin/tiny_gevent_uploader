#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

from flask import Flask
from flask import request
import os
from flask import render_template
import re
from flask_uwsgi_websocket import GeventWebSocket
import gevent
from flask import copy_current_request_context

UPLOAD_FOLDER = '/tmp'
ADDR = '127.0.0.1:7192'

if 'TGU_UPLOAD' in os.environ:
    UPLOAD_FOLDER = os.environ['TGU_UPLOAD']
if 'TGU_ADDR' in os.environ:
    ADDR = os.environ['TGU_ADDR']
print 'UPLOAD_FOLDER', UPLOAD_FOLDER
print 'ADDR', ADDR

application = Flask(__name__, template_folder='.')
websocket = GeventWebSocket(application)

jobs = {}


def current_milli_time():
    return int(round(time.time() * 1000))


@websocket.route('/websocket')
def echo(ws):
    with application.request_context(ws.environ):
        job_id = int(request.args.get('job_id'))
        if job_id not in jobs:
            print "no such job", job_id
            return
        while True:
            msg = ws.receive()
            if msg is not None:
                if jobs[job_id]['file_size'] == 0:
                    ws.send(str(100))
                else:
                    result = jobs[job_id]['result'] * 100 / jobs[job_id]['file_size']
                    ws.send(str(result))
                print 'sent to socket', jobs[job_id]
            else:
                return


def truncate_file(file_name):
    """ http://stackoverflow.com/a/10289740/1319505
    :param file_name: file_name
    """
    f = open(file_name, "r+")

    # Move the pointer (similar to a cursor in a text editor) to the end of the file.
    f.seek(0, os.SEEK_END)

    # This code means the following code skips the very last character in the file -
    # i.e. in the case the last line is null we delete the last line
    # and the penultimate one
    pos = f.tell() - 1

    # Read each character in the file one at a time from the penultimate
    # character going backwards, searching for a newline character
    # If we find a new line, exit the search
    while pos > 0 and f.read(1) != "\n":
        pos -= 1
        f.seek(pos, os.SEEK_SET)

    # So long as we're not at the start of the file, delete all the characters ahead of this position
    if pos > 0:
        f.seek(pos - 1, os.SEEK_SET)
        f.truncate()

    f.close()


def process_file(job_id):
    gevent.sleep(0.001)
    total = 0
    file_path = UPLOAD_FOLDER + "/" + jobs[job_id]['file_name']
    jobs[job_id]['file_size'] = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        byte = f.read(1)
        while byte:
            total += 1
            #: no sense to make it in this block but the load
            jobs[job_id]['result'] = total
            byte = f.read(1)
            if total % 1024 == 0:
                gevent.sleep(0)
        jobs[job_id]['complete'] = True
        print "complete: ", jobs[job_id]


def download_file(job_id):
    gevent.sleep(0.001)

    #: parsing multipart form data to get the filename
    #: example:
    #:  ------WebKitFormBoundarylRvYKzQqFCAXurl5
    #: Content-Disposition: form-data; name="file"; filename="1.jpg"
    #: Content-Type: image/jpeg
    #: BLANK LINE
    #: CONTENT
    chunk_size = 1024
    pat = re.compile("filename=\"(.*?)\"")
    chunk = request.stream.read(chunk_size)
    data = chunk.split("\n", 4)
    match = re.search(pat, data[1])
    if not match:
        pass

    file_name = match.group(1)
    jobs[job_id]['file_name'] = file_name

    with open(UPLOAD_FOLDER + "/" + file_name, "wb") as f:
        f.write(data[4])

        chunk_size = 1024 * 512
        while True:
            chunk = request.stream.read(chunk_size)
            gevent.sleep(0)
            if len(chunk) == 0:
                break
            f.write(chunk)

    # TODO: move this ugly, but simple code to chunk processing, want to sleep so much
    # remove last 2 lines
    truncate_file(UPLOAD_FOLDER + "/" + file_name)


@application.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method != 'POST':
        return str(0)

    job_id = current_milli_time()
    jobs[job_id] = {
        'file_name': None,
        'result': 0,
        'file_size': 0,
        'complete': False,
        'content_length': request.content_length,
    }

    print "job started", job_id, jobs[job_id]

    @copy_current_request_context
    def wrap_download_file():
        download_file(job_id)

    gevent.joinall([
        gevent.spawn(wrap_download_file),
    ])

    @copy_current_request_context
    def wrap_process_file():
        process_file(job_id)

    gevent.spawn(wrap_process_file)

    return str(job_id)


@application.route("/")
def request_hello():
    return render_template("page.html", addr=ADDR)


if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)
