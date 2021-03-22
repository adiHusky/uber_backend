from flask import Flask, flash, request, jsonify, render_template, redirect, url_for, g, session, send_from_directory, abort
from flask_cors import CORS
# from flask import status
from datetime import date, datetime, timedelta
from calendar import monthrange
from dateutil.parser import parse
import pytz
import os
import sys
import time
import uuid
import json
import random
import string
import pathlib
import io
from uuid import UUID
from bson.objectid import ObjectId

# straight mongo access
from pymongo import MongoClient
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://acea88276810494e96828c4fd0e1471f@o555579.ingest.sentry.io/5685529",
    integrations=[FlaskIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,

    # By default the SDK will try to use the SENTRY_RELEASE
    # environment variable, or infer a git commit
    # SHA as release, however you may want to set
    # something more human-readable.
    # release="myapp@1.0.0",
)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


# mongo
# mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_client = MongoClient(
    "mongodb+srv://Mahitha-Maddi:Mahitha%4042@cluster0.1z0g8.mongodb.net/test")

app = Flask(__name__)
# CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})
basedir = os.path.abspath(os.path.dirname(__file__))

# Here are my datasets
bookings = dict()


################
# Apply to mongo
################

def atlas_connect():
    # Node
    # const MongoClient = require('mongodb').MongoClient;
    # const uri = "mongodb+srv://admin:<password>@tweets.8ugzv.mongodb.net/myFirstDatabase?retryWrites=true&w=majority";
    # const client = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true });
    # client.connect(err => {
    # const collection = client.db("test").collection("devices");
    # // perform actions on the collection object
    # client.close();
    # });

    # Python
    client = pymongo.MongoClient(
        "mongodb+srv://Mahitha-Maddi:Mahitha%4042@cluster0.1z0g8.mongodb.net/test")
    db = client.test


# database access layer
def insert_one(r):
    start_time = datetime.now()
    with mongo_client:
        # start_time_db = datetime.now()
        db = mongo_client['Uber']
        # microseconds_caching_db = (datetime.now() - start_time_db).microseconds
        # print("*** It took " + str(microseconds_caching_db) + " microseconds to cache mongo handle.")

        print("...insert_one() to mongo: ", r)
        try:
            mongo_collection = db['bookings']
            result = mongo_collection.insert_one(r)
            print("inserted _ids: ", result.inserted_id)
        except Exception as e:
            print(e)

    microseconds_doing_mongo_work = (datetime.now() - start_time).microseconds
    print("*** It took " + str(microseconds_doing_mongo_work) +
          " microseconds to insert_one.")


def tryexcept(requesto, key, default):
    lhs = None
    try:
        lhs = requesto.json[key]
        # except Exception as e:
    except:
        lhs = default
    return lhs


def ssm():
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return str((now - midnight).seconds)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


# endpoint to check Availability
@app.route("/checkAvailability", methods=["POST"])
def check_availability():
    source = request.json['source']
    destination = request.json['destination']
    date = request.json['date']
    with mongo_client:
        #raise InvalidUsage('This view is gone', status_code=410)
        db = mongo_client['Uber']
        mongo_collection = db['available']
        print(source)

        myquery = {"source": {"$regex": str(source)}, "destination": {
            "$regex": str(destination)}, "date": {"$regex": str(date)}}
        cursor = dict()
        cursor = mongo_collection.find(myquery, {"_id": 0})
        records = list(cursor)
        howmany = len(records)
        print('found ' + str(howmany) + ' bookings!')
        sorted_records = sorted(records, key=lambda t: t['source'])
        print(type(sorted_records))
    return jsonify(sorted_records)

# endpoint to create new Booking


@app.route("/book", methods=["POST"])
def book_bus():
    source = request.json['source']
    destination = request.json['destination']
    date = request.json['date']
    startTime = request.json['startTime']
    endTime = request.json['endTime']
    user = request.json['user']
    busnumber = request.json['busnumber']
    booking = dict(user=user, source=source, destination=destination, busnumber=busnumber,
                   date=date, startTime=startTime, endTime=endTime, bookeddate=datetime.now(
                   ).strftime("%Y-%m-%d %H:%M:%S"),
                   _id=str(ObjectId()))

    insert_one(booking)
    return jsonify(booking)


@app.route("/bookings-results", methods=["GET"])
def get_tweets_results():
    global bookings
    with mongo_client:
        db = mongo_client['Uber']
        mongo_collection = db['bookings']

        cursor = mongo_collection.find({})
        records = list(cursor)
        howmany = len(records)
        print('found ' + str(howmany) + ' bookings!')
        sorted_records = sorted(records, key=lambda t: t['source'])
    return jsonify(sorted_records)

##################
# Apply from mongo
##################


def applyRecordLevelUpdates():
    return None


def applyCollectionLevelUpdates():
    global bookings
    with mongo_client:
        db = mongo_client['Uber']
        mongo_collection = db['available']

        cursor = mongo_collection.find({})
        records = list(cursor)
        # bookings[0] = records[0]

        howmany = len(records)
        print('found ' + str(howmany) + ' bookings!')
        sorted_records = sorted(records, key=lambda t: t['source'])
        # return json.dumps({"results": sorted_records })

        for booking in sorted_records:
            bookings[booking['_id']] = booking


@app.route("/")
def home():
    return """Welcome to Uber backend!<br/>"""
##################
# ADMINISTRATION #
##################

# This runs once before the first single request
# Used to bootstrap our collections


@app.before_first_request
def before_first_request_func():
    applyCollectionLevelUpdates()

# This runs once before any request


@app.before_request
def before_request_func():
    applyRecordLevelUpdates()


############################
# INFO on containerization #
############################
# To containerize a flask app:
# https://pythonise.com/series/learning-flask/building-a-flask-app-with-docker-compose
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
