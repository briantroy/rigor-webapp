#!/usr/bin/env python

from __future__ import division
import os
import sys
import time
import random
import json

import functools

from flask import Flask
from flask import render_template
from flask import send_file
from flask import jsonify
from flask import request
from flask import Response
from flask import abort
from flask import redirect

from utils import *
import backend
import config


#--------------------------------------------------------------------------------
# HELPERS

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'blindsight' and password == 'rigor!!!!!'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def use_basic_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


#--------------------------------------------------------------------------------
# FLASK

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fpqf94y1och48OUGWO38yfoo8yroihf28y982heD'


#--------------------------------------------------------------------------------
# ROUTING

def simulateSlow():
    if config.CROWD_FAKE_SLOW_DELAY > 0:
        time.sleep(config.CROWD_FAKE_SLOW_DELAY)

@app.route('/')
# @use_basic_auth
def index():
    simulateSlow()
    return render_template('crowd_index.html')

@app.route('/stats')
def stats():
    """
    {
        words_raw: 29,
        words_verified: 29,
        words_sliced: 29,
        words_total: 104,
    }
    """
    simulateSlow()
    return jsonify(backend.getCrowdStats(config.CROWD_DB))

@app.route('/photos')
def photos():
    simulateSlow()
    return render_template('crowd_index.html')

@app.route('/words')
def words():
    simulateSlow()
    return render_template('crowd_words.html')

@app.route('/words/<annotation_id>')
def wordsWithId(annotation_id):
    simulateSlow()
    return render_template('crowd_words.html')

@app.route('/word/next')
def redirectToNextWord():
    simulateSlow()
    annotation_id = backend.getNextCrowdWord(config.CROWD_DB)
    if annotation_id is None:
        abort(404)
    else:
        return redirect('/word/%s'%annotation_id)

@app.route('/word/<annotation_id>')
def getWord(annotation_id):
    """
    {
        annotation_id
        model
        image_id
        image_url  # added here, not from backend
        x_res
        y_res
        ext
        chars = [
            {
                start
                end
                model
            },
            { ... }
        ]
    }
    """
    simulateSlow()
    word = backend.getCrowdWord(config.CROWD_DB, annotation_id)

    word['image_url'] = '/word/%s.%s' % (word['annotation_id'], word['ext'])
    del word['image_path']

    return jsonify(word)

@app.route('/word/<annotation_id>.<ext>')
def getWordImage(annotation_id, ext):
    simulateSlow()
    path = backend.getCrowdWordImagePath(config.CROWD_DB, annotation_id, ext)
    if os.path.exists(path):
        return send_file(path)
    else:
        abort(404)

@app.route('/word/save', methods=['POST'])
def saveWord():
    simulateSlow()
    wordData = json.loads(request.data)
    backend.saveCrowdWord(config.CROWD_DB, wordData)
    return 'ok'

#--------------------------------------------------------------------------------
# MAIN

if __name__ == '__main__':
    print '--------------------------------------------------------------------------------'
    debugMain('ready')
    ARGS = sys.argv[1:]
    if len(ARGS) != 1:
        print 'usage: crowd_app.py PORTNUMBER'
        sys.exit(0)
    port = int(ARGS[0])
    app.run(debug=True, port=port, host='0.0.0.0', use_evalex=False)

