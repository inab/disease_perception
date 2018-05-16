#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask import Flask
from flask_restplus import Api, Namespace, Resource, fields
import sqlite3
import urllib


# This class manages all the database queries
class ComorbiditiesNetwork(object):
	def __init__(self,dbpath,api,itersize=100):
		self.api = api
		self.db = sqlite3.connect('file:'+urllib.parse.quote(dbpath)+'?mode=ro',uri=True, check_same_thread=False)
		self.dbpath = dbpath
		self.itersize = itersize
	
	def _getCursor(self):
		cur = self.db.cursor()
		cur.arraysize = self.itersize
		return cur
		
	def genes(self):
		res = []
		cur = self._getCursor()
		try:
			cur.execute('SELECT gene_symbol FROM gene')
			while True:
				genes = cur.fetchmany()
				if len(genes)==0:
					break
				
				res.extend(map(lambda gene: {'symbol': gene[0]},genes))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def gene(self,symbol):
		res = None
		cur = self._getCursor()
		try:
			cur.execute('SELECT gene_symbol,ensembl_id,uniprot_id FROM gene WHERE gene_symbol = ?',(symbol,))
			while True:
				gene = cur.fetchone()
				if gene is not None:
					res = {
						'symbol': gene[0],
						'ensembl_id': gene[1],
						'uniprot_acc': gene[2]
					}
				else:
					self.api.abort(404, "Gene {} is not found in the database".format(symbol))
				break
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def drugs(self):
		res = []
		cur = self._getCursor()
		try:
			cur.execute('SELECT id,name FROM drug')
			while True:
				drugs = cur.fetchmany()
				if len(drugs)==0:
					break
				
				res.extend(map(lambda drug: {'id': drug[0],'name': drug[1]},drugs))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def drug(self,id):
		res = None
		cur = self._getCursor()
		try:
			cur.execute('SELECT id,name FROM drug WHERE id = ?',(id,))
			while True:
				drug = cur.fetchone()
				if drug is not None:
					res = {
						'id': drug[0],
						'name': drug[1]
					}
				else:
					self.api.abort(404, "Drug {} is not found in the database".format(id))
				
				break
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res

	@staticmethod
	def _formatStudy(study_id):
		return {'id': study_id,'source': 'GEO'  if study_id.startswith('GSE')  else 'ArrayExpress' }
	
	def studies(self):
		res = []
		cur = self._getCursor()
		try:
			cur.execute('SELECT geo_arrayexpress_code FROM study')
			while True:
				studies = cur.fetchmany()
				if len(studies)==0:
					break
				
				res.extend(map(lambda study: ComorbiditiesNetwork._formatStudy(study[0]) ,studies))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def study(self,study_id):
		res = None
		cur = self._getCursor()
		try:
			cur.execute('SELECT geo_arrayexpress_code FROM study WHERE geo_arrayexpress_code = ?',(study_id,))
			while True:
				study = cur.fetchone()
				if study is not None:
					res = ComorbiditiesNetwork._formatStudy(study[0])
				else:
					self.api.abort(404, "Study {} is not found in the database".format(study_id))
				
				break
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res


app = Flask(__name__)
api = Api(app, version='0.1', title='Comorbidities Network REST API',
	description='A simple comorbidites network exploring API which is used by the web explorer',
	default='cm',
	license='AGPL-3',
	default_label='Comorbidities network queries'
)

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

# This is the singleton instance shared by all the resources

# Creating the object holding the state of the API
if hasattr(sys, 'frozen'):
	basis = sys.executable
else:
	basis = sys.argv[0]

api_root = os.path.split(basis)[0]

# Connection to the database
dbpath = os.path.join(api_root,'DB','net_comorbidity.db')
CMNetwork = ComorbiditiesNetwork(dbpath,api)


# Now, the different namespaces
ns = Namespace('cm','Comorbidities network info')
api.add_namespace(ns)



genes_ns = Namespace('genes','Comorbidities related genes')
api.add_namespace(genes_ns,path='/genes')
# Now, the routes
@genes_ns.route('')
class GeneList(Resource):
	'''Shows a list of all the genes related in comorbidities'''
	@genes_ns.doc('list_genes')
	@genes_ns.marshal_list_with(simple_gene_model)
	def get(self):
		'''List all genes'''
		return CMNetwork.genes()

@genes_ns.route('/<symbol>')
@genes_ns.response(404, 'Gene not found')
@genes_ns.param('symbol', 'The gene symbol')
class Gene(Resource):
	'''Return the detailed information of a gene'''
	@genes_ns.doc('gene')
	@genes_ns.marshal_with(gene_model)
	def get(self,symbol):
		'''It gets detailed gene information'''
		return CMNetwork.gene(symbol)


drugs_ns = Namespace('drugs','Comorbidities related drugs')
api.add_namespace(drugs_ns,path='/drugs')

@drugs_ns.route('')
class DrugList(Resource):
	'''Shows a list of all the drugs related in comorbidity studies'''
	@drugs_ns.doc('list_drugs')
	@drugs_ns.marshal_list_with(simple_drug_model)
	def get(self):
		'''List all drugs involved in the different studies'''
		return CMNetwork.drugs()

@drugs_ns.route('/<int:id>')
@drugs_ns.response(404, 'Drug not found')
@drugs_ns.param('id', 'The drug id')
class Drug(Resource):
	'''Return the detailed information of a drug'''
	@drugs_ns.doc('drug')
	@drugs_ns.marshal_with(drug_model)
	def get(self,id):
		'''It gets detailed drug information'''
		return CMNetwork.drug(id)


studies_ns = Namespace('studies','Comorbidities related studies')
api.add_namespace(studies_ns,path='/studies')

@studies_ns.route('')
class StudyList(Resource):
	'''Shows a list of all the studies used to build the comorbidity network'''
	@studies_ns.doc('list_studies')
	@studies_ns.marshal_list_with(simple_study_model)
	def get(self):
		'''List all the studies used to build the comorbidity network'''
		return CMNetwork.studies()

@studies_ns.route('/<study_id>')
@studies_ns.response(404, 'Study not found')
@studies_ns.param('study_id', 'The study id')
class Study(Resource):
	'''Return the detailed information of a study'''
	@studies_ns.doc('study')
	@studies_ns.marshal_with(study_model)
	def get(self,study_id):
		'''It gets detailed study information'''
		return CMNetwork.study(study_id)



if __name__ == '__main__':
	app.run(debug=True)
