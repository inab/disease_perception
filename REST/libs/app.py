#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask import Flask, Blueprint, redirect
from flask_restplus import Api, Namespace, Resource
from flask_cors import CORS
from flask_compress import Compress

from .cm_queries import ComorbiditiesNetwork

from .res.ns import ROUTES as ROOT_ROUTES
from .res.genes import ROUTES as GENE_ROUTES
from .res.drugs import ROUTES as DRUG_ROUTES
from .res.studies import ROUTES as STUDY_ROUTES
from .res.diseases import ROUTES as DISEASE_ROUTES
from .res.patients import ROUTES as PATIENT_ROUTES

ROUTE_SETS = [
	ROOT_ROUTES,
	GENE_ROUTES,
	DRUG_ROUTES,
	STUDY_ROUTES,
	DISEASE_ROUTES,
	PATIENT_ROUTES
]

def _register_cm_namespaces(api,res_kwargs):
	for route_set in ROUTE_SETS:
		ns = route_set['ns']
		api.add_namespace(ns,route_set['path'])
		for route in route_set['routes']:
			ns.add_resource(route[0],route[1],resource_class_kwargs=res_kwargs)

def init_comorbidities_app(local_config):
	#app = Flask('como_network',static_url_path='/',static_folder='static')
	app = Flask('como_network')
	
	# It must be done after app is initialized
	# in order to avoid circular dependencies
	#
	# https://explore-flask.readthedocs.io/en/latest/views.html#custom-converters
	from .converters import ListConverter

	app.url_map.converters['list'] = ListConverter

	blueprint = Blueprint('api','como_network_api')
	blueprint_static = Blueprint('frontend','como_network_frontend',static_url_path='/',static_folder='static')

	@blueprint_static.route('/')
	def root():
		return app.send_static_file('index.html')
		#return redirect('./index.html')


	# This enables CORS along all the app
	cors = CORS(app)
	
	# This enables compression
	compress = Compress(app)

	# Attaching the API to the app 
	api = Api(
		app=blueprint,
		version='0.4.0',
		title='Disease PERCEPTION REST API',
		description='A simple comorbidites network exploring API which is used by the Disease PERCEPTION explorer',
		default='cm',
		license='AGPL-3',
		default_label='Disease Perception queries'
	)
	
	# This is the singleton instance shared by all the resources
	dbpath = local_config['db']
	CMNetwork = ComorbiditiesNetwork(dbpath, api)
	
	res_kwargs = {'cmnetwork': CMNetwork}
	
	_register_cm_namespaces(api,res_kwargs)
	
	# Adding the two containers: API + frontend
	app.register_blueprint(blueprint,url_prefix='/api')
	app.register_blueprint(blueprint_static,url_prefix='/')
	
	return app
