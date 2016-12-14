from flask import Flask, request
from multiprocessing import Pool
from boto.s3.key import Key
import tempfile
import datetime
import sys, os
import json
import boto
import time

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
BUCKET_NAME = 'hackdays'
app = Flask(__name__)

def download_week_file(week, year):
    conn = boto.connect_s3(
        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY
    )

    bucket = conn.get_bucket(BUCKET_NAME)
    file_path = 'foosball/week-%s-%s.json' % (week, year)
    key = Key(bucket, file_path)

    f = open("/tmp/blah.%s.json" % time.time(), 'wr+')

    try:
	key.get_contents_to_filename(f.name)
	f.seek(0)
	result = json.load(f)
    except boto.exception.S3ResponseError as e:
	result = {
	    "meta": {"updated": 0},
	    "games": [],
	    "teams": {
		"0": {
		    "name": "Pink",
		    "players": []
		},
		"1": {
		    "name": "Blue",
		    "players": []
		}
	    }
	}

    os.unlink(f.name)
    f.close()

def upload_week_file(stat, week, year):
    stat['meta']['updated'] = int(time.time())

    conn = boto.connect_s3(
        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY
    )

    bucket = conn.get_bucket(BUCKET_NAME)
    key = Key(bucket, 'foosball/week-%s-%s.json' % (week, year))

    with tempfile.NamedTemporaryFile() as temp_file:
	temp_file.write(json.dumps(stat))
	temp_file.flush()
	key.set_contents_from_filename(temp_file.name)

    key.set_acl('public-read-write')

def update_stat_sync(stat, current_week, current_year):
    stats = download_week_file(current_week, current_year)
    stats['games'].append(stat)
    upload_week_file(stats, current_week, current_year)

def update_stat_async(stat, current_week, current_year):
    pool.apply_async(update_stat_sync, (stat, current_week, current_year))

@app.route('/')
def index():
    return 'stat api running'

@app.route('/stat', methods=['POST'])
def stat():
    stat = json.loads(request.data)
    current_week = datetime.datetime.now().isocalendar()[1]
    current_year = datetime.datetime.now().isocalendar()[0]
    update_stat_async(stat, current_week, current_year)
    return '', 202

if __name__ == '__main__':
    pool = Pool(processes=4)
    app.run()
