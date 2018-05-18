#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask import Flask
from flask_restplus import Api, Namespace, Resource
from flask_cors import CORS

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

def init_comorbidities_app(dbpath):
	app = Flask('como_network')

	# This enables CORS along all the app
	cors = CORS(app)

	# Attaching the API to the app 
	api = Api(
		app,
		version='0.3',
		title='Comorbidities Network REST API',
		description='A simple comorbidites network exploring API which is used by the web explorer',
		default='cm',
		license='AGPL-3',
		default_label='Comorbidities network queries'
	)
	
	# This is the singleton instance shared by all the resources
	CMNetwork = ComorbiditiesNetwork(dbpath,api)
	
	res_kwargs = {'cmnetwork': CMNetwork}
	
	_register_cm_namespaces(api,res_kwargs)
	
	return app