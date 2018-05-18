#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask_restplus import Namespace, Api, Resource, fields

class CMResource(Resource):
	'''This class eases passing the instance of the comorbidity network query API'''
	def __init__(self,api=None,*args,**kwargs):
		super().__init__(api,*args,**kwargs)
		self.cmn = kwargs['cmnetwork']



NS = Namespace('cm','Comorbidities network info')
#ns = api.namespace('cm', description='Comorbidities network queries')


GENES_NS = Namespace('genes','Comorbidities related genes')
# The different models
#simple_gene_model = GENES_NS.schema_model('SimpleGene', {
#	'properties': {
#		'symbol': {
#			'type': 'string',
#			'description': 'The gene symbol'
#		}
#	},
#	'type': 'object',
#	'required': [ 'symbol' ]
#})

simple_gene_model = GENES_NS.model('SimpleGene', {
	'symbol': fields.String(required=True,description = 'The gene symbol'),
})

#gene_model = GENES_NS.schema_model('Gene', {
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

gene_model = GENES_NS.model('Gene', {
	'symbol': fields.String(required=True,description = 'The gene symbol'),
	'ensembl_id': fields.String(description = 'The EnsEMBL gene id'),
	'uniprot_acc': fields.String(description = 'The UniProt Accession Number')
})


DRUGS_NS = Namespace('drugs','Comorbidities related drugs')

#drug_model = DRUGS_NS.schema_model('Drug', {
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

drug_model = DRUGS_NS.model('Drug', {
	'id': fields.Integer(required=True, description = 'The internal id of the drug'),
	'name': fields.String(required=True, description = 'The drug name')
})

simple_drug_model = drug_model


STUDIES_NS = Namespace('studies','Comorbidities related studies')

#study_model = STUDIES_NS.schema_model('Study', {
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

study_model = STUDIES_NS.model('Study', {
	'id': fields.String(required=True, description = 'The id of the study in the original source'),
	'source': fields.String(required=True, description = 'The study source')
})

simple_study_model = study_model

DG_NS = Namespace('disease_groups','Disease groups')

#simple_disease_group_model = DG_NS.schema_model('DiseaseGroup', {
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

simple_disease_group_model = DG_NS.model('SimpleDiseaseGroup', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease group'),
	'name': fields.String(required=True, description = 'The disease group symbolic name')
})

disease_group_model = DG_NS.model('DiseaseGroup', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease group'),
	'name': fields.String(required=True, description = 'The disease group symbolic name'),
	'color': fields.String(required=True, description = 'Preferred color for this group of diseases')
})


DISEASE_NS = Namespace('diseases','Diseases')

simple_disease_model = DISEASE_NS.model('SimpleDisease', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease'),
	'disease_group_id': fields.Integer(required=True, description = 'The internal id of the disease group where this disease is classified into'),
	'name': fields.String(required=True, description = 'The disease symbolic name')
})

disease_model = DISEASE_NS.model('Disease', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease'),
	'disease_group_id': fields.Integer(required=True, description = 'The internal id of the disease group where this disease is classified into'),
	'name': fields.String(required=True, description = 'The disease symbolic name'),
	'color': fields.String(required=True, description = 'Preferred color for this group of diseases'),
	'icd9': fields.String(description = 'The ICD9 code of this disease'),
	'icd10': fields.String(description = 'The ICD10 code of this disease')
})


PSG_NS = Namespace('patient_subgroups','Patient subgroups')
