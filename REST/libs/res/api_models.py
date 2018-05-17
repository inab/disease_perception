#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask_restplus import Api, Resource, fields

class CMResource(Resource):
	'''This class eases passing the instance of the comorbidity network query API'''
	def __init__(self,api=None,*args,**kwargs):
		super().__init__(api,*args,**kwargs)
		self.cmn = kwargs['cmnetwork']



api = Api(
	version='0.2',
	title='Comorbidities Network REST API',
	description='A simple comorbidites network exploring API which is used by the web explorer',
	default='cm',
	license='AGPL-3',
	default_label='Comorbidities network queries'
)

def init_comorbidities_api(app):
	api.app = app
	api.init_app(app)
	
	return api


#ns = api.namespace('cm', description='Comorbidities network queries')

# The different models
#simple_gene_model = api.schema_model('SimpleGene', {
#	'properties': {
#		'symbol': {
#			'type': 'string',
#			'description': 'The gene symbol'
#		}
#	},
#	'type': 'object',
#	'required': [ 'symbol' ]
#})

simple_gene_model = api.model('SimpleGene', {
	'symbol': fields.String(required=True,description = 'The gene symbol'),
})

#gene_model = api.schema_model('Gene', {
#	'properties': {
#		'symbol': {
#			'type': 'string',
#			'description': 'The gene symbol'
#		},
#		'ensembl_id': {
#			'type': 'string',
#			'pattern': '^ENSG[0-9]{11}$',
#			'description': 'The EnsEMBL gene id'
#		},
#		'uniprot_acc': {
#			'type': 'string',
#			'description': 'The UniProt Accession Number'
#		}
#	},
#	'type': 'object',
#	'required': [ 'symbol' ]
#})

gene_model = api.model('Gene', {
	'symbol': fields.String(required=True,description = 'The gene symbol'),
	'ensembl_id': fields.String(description = 'The EnsEMBL gene id'),
	'uniprot_acc': fields.String(description = 'The UniProt Accession Number')
})


#drug_model = api.schema_model('Drug', {
#	'description': 'A drug stored in the comorbidities database',
#	'properties': {
#		'id': {
#			'type': 'string',
#			'description': 'The internal id of the drug'
#		},
#		'name': {
#			'type': 'string',
#			'description': 'The drug name'
#		}
#	},
#	'type': 'object',
#	'required': ['id','name']
#})

drug_model = api.model('Drug', {
	'id': fields.Integer(required=True, description = 'The internal id of the drug'),
	'name': fields.String(required=True, description = 'The drug name')
})

simple_drug_model = drug_model


#study_model = api.schema_model('Study', {
#	'description': 'A study stored in the comorbidities database',
#	'properties': {
#		'id': {
#			'type': 'string',
#			'description': 'The id of the study in the original source'
#		},
#		'source': {
#			'type': 'string',
#			'description': 'The study source',
#			'enum': [ 'GEO', 'ArrayExpress' ]
#		}
#	},
#	'type': 'object',
#	'required': ['id','source']
#})

study_model = api.model('Study', {
	'id': fields.String(required=True, description = 'The id of the study in the original source'),
	'source': fields.String(required=True, description = 'The study source')
})

simple_study_model = study_model


#simple_disease_group_model = api.schema_model('DiseaseGroup', {
#	'description': 'A disease group describedç in the comorbidities database',
#	'properties': {
#		'id': {
#			'type': 'string',
#			'description': 'The internal id of the disease group'
#		},
#		'name': {
#			'type': 'string',
#			'description': 'The disease group symbolic name'
#		}
#	},
#	'type': 'object',
#	'required': ['id','name']
#})

simple_disease_group_model = api.model('SimpleDiseaseGroup', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease group'),
	'name': fields.String(required=True, description = 'The disease group symbolic name')
})

disease_group_model = api.model('DiseaseGroup', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease group'),
	'name': fields.String(required=True, description = 'The disease group symbolic name'),
	'color': fields.String(required=True, description = 'Preferred color for this group of diseases')
})


simple_disease_model = api.model('SimpleDisease', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease'),
	'disease_group_id': fields.Integer(required=True, description = 'The internal id of the disease group where this disease is classified into'),
	'name': fields.String(required=True, description = 'The disease symbolic name')
})

disease_model = api.model('Disease', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease'),
	'disease_group_id': fields.Integer(required=True, description = 'The internal id of the disease group where this disease is classified into'),
	'name': fields.String(required=True, description = 'The disease symbolic name'),
	'color': fields.String(required=True, description = 'Preferred color for this group of diseases'),
	'icd9': fields.String(description = 'The ICD9 code of this disease'),
	'icd10': fields.String(description = 'The ICD10 code of this disease')
})
