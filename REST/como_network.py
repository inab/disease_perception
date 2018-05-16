#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask import Flask
from flask_restplus import Api, Resource, fields
import sqlite3
import urllib

app = Flask(__name__)
api = Api(app, version='0.1', title='Comorbidities Network REST API',
	description='A simple comorbidites network exploring API which is used by the web explorer',
	default='cm',
	license='AGPL-3',
	default_label='Comorbidities network queries'
)

ns = api.namespace('cm', description='Comorbidities network queries')

simple_gene_model = api.model('SimpleGene', {
	'symbol': fields.String(required=True, description='The gene symbol')
})

gene_model = api.model('Gene', {
	'symbol': fields.String(required=True, description='The gene symbol'),
	'ensembl_id': fields.String(required=True, description='The EnsEMBL gene id'),
	'uniprot_acc': fields.String(required=True, description='The UniProt Accession Number') 
})

drug_model = api.model('Drug', {
	'id': fields.String(required=True, description='The internal id of the drug'),
	'name': fields.String(required=True, description='The drug name')
})

simple_drug_model = drug_model

# This class manages all the database queries
class ComorbiditiesNetwork(object):
	def __init__(self,dbpath,itersize=100):
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
					api.abort(404, "Gene {} is not found in the database".format(symbol))
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
					api.abort(404, "Drug {} is not found in the database".format(id))
				
				break
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res

# Creating the object holding the state of the API
if hasattr(sys, 'frozen'):
	basis = sys.executable
else:
	basis = sys.argv[0]

api_root = os.path.split(basis)[0]

# Connection to the database
dbpath = os.path.join(api_root,'DB','net_comorbidity.db')
CMNetwork = ComorbiditiesNetwork(dbpath)

# Now, the routes
@ns.route('/genes')
class GeneList(Resource):
	'''Shows a list of all the genes related in comorbidities'''
	@ns.doc('list_genes')
	@ns.marshal_list_with(simple_gene_model)
	def get(self):
		'''List all genes'''
		return CMNetwork.genes()

	@ns.route('/genes/<symbol>')
	@ns.response(404, 'Gene not found')
	@ns.param('symbol', 'The gene symbol')
	class Gene(Resource):
		'''Return the detailed information of a gene'''
		@ns.doc('gene')
		@ns.marshal_with(gene_model)
		def get(self,symbol):
			'''It gets detailed gene information'''
			return CMNetwork.gene(symbol)

@ns.route('/drugs')
class DrugList(Resource):
	'''Shows a list of all the drugs related in comorbidity studies'''
	@ns.doc('list_drugs')
	@ns.marshal_list_with(simple_drug_model)
	def get(self):
		'''List all drugs involved in the different studies'''
		return CMNetwork.drugs()

	@ns.route('/drugs/<int:id>')
	@ns.response(404, 'Drug not found')
	@ns.param('id', 'The drug id')
	class Drug(Resource):
		'''Return the detailed information of a drug'''
		@ns.doc('drug')
		@ns.marshal_with(drug_model)
		def get(self,id):
			'''It gets detailed drug information'''
			return CMNetwork.drug(id)


if __name__ == '__main__':
	app.run(debug=True)
