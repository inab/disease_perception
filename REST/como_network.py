#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

from flask import Flask
from flask_restplus import Api, Resource, fields
import sqlite3

app = Flask(__name__)
api = Api(app, version='0.1', title='Comorbidities Network REST API',
	description='A simple comorbidites network exploring API which is used by the web explorer',
)

ns = api.namespace('cm', description='Comorbidities network queries')

#todo = api.model('Todo', {
#	'id': fields.Integer(readOnly=True, description='The task unique identifier'),
#	'task': fields.String(required=True, description='The task details')
#})

class ComorbiditiesNetwork(object):
	def __init__(self):
		# Connection to the database



class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
    app.run(debug=True)
