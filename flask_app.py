#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/05/08 23:31:49
#   License :   Apache 2.0 (See LICENSE)
#

'''
The Flask application, containing the WebAPI and the WebApplication in the future.
It may be split into multiple modules when necessary.
'''

from flask import Flask, redirect, request
from flask_restful import Api, Resource, fields, marshal_with, reqparse
import uuid

from storage import App

import model
import sede
import utils

DB_DIRECTORY = 'data'
API_BASE_URL='/api'

iapp = App(DB_DIRECTORY)

app = Flask(__name__)

api = Api(app)

### WebAPI begin

def pre_handle_event_post_request(id):
    parser = reqparse.RequestParser()
    parser.add_argument('title', required=True, help='The title of the event.')
    parser.add_argument('desc', default=None, help='The detailed description of the event.')
    parser.add_argument('before', type=utils.comma_separated_list, default=[], help='Any other entries that are before this item. Represented as a comma-separated list of the entry IDs.')
    parser.add_argument('after', type=utils.comma_separated_list, default=[], help='Any other entries that are after this item. Represented as a comma-separated list of the entry IDs.')
    parser.add_argument('same', type=utils.comma_separated_list, default=[], help='Any other entries that are at the same time as this item. Represented as a comma-separated list of the entry IDs.')
    args = parser.parse_args(strict=True)
    builder = model.EventBuilder(args.title).desc(args.desc).id(id)
    for before in args.before:
        builder.before(before)
    for after in args.after:
        builder.after(after)
    for same in args.same:
        builder.same(same)
    event = builder.build()
    return event

class EventList(Resource):
    def __init__(self, app):
        self.app = app

    def get(self):
        return [str(item) for item in self.app.collection().list()]

    def post(self):
        id = uuid.uuid4()
        # return redirect(api.url_for(Event, id=str(id)), code=307)
        event = pre_handle_event_post_request(str(id))
        self.app.collection().add_item(event)
        return str(id)

class Event(Resource):
    def __init__(self, app):
        self.app = app

    def get(self, id):
        event = self.app.collection().get_event(id)
        return sede.serialise_event(event)

    def post(self, id):
        event = pre_handle_event_post_request(id)
        self.app.collection().update_item(id, event)
        return id

class Collection(Resource):
    def __init__(self, app):
        self.app = app

    def get(self):
        return {
                'is_self_contained': self.app.collection().is_self_contained(),
                'has_no_conflict': self.app.collection().has_no_conflict(),
                'conflicts': self.app.collection().conflicts(),
                }

api.add_resource(EventList, f'{API_BASE_URL}/event',
        resource_class_args=[iapp])
api.add_resource(Event, f'{API_BASE_URL}/event/<string:id>',
        resource_class_args=[iapp])
api.add_resource(Collection, f'{API_BASE_URL}/collection',
        resource_class_args=[iapp])

### WebAPI end


if __name__ == '__main__':
    app.run(debug=True)
