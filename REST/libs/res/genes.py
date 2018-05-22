#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResource, GENES_NS, gene_model

# Now, the routes
#@GENES_NS.route('',resource_class_kwargs={'cmnetwork': CMNetwork})
class GeneList(CMResource):
	'''Shows a list of all the genes related in comorbidities'''
	@GENES_NS.doc('list_genes')
	@GENES_NS.marshal_list_with(gene_model)
	def get(self):
		'''List all genes'''
		#return CMNetwork.genes()
		return self.cmn.genes()

#@GENES_NS.route('/<symbol>',resource_class_kwargs={'cmnetwork': CMNetwork})
@GENES_NS.response(404, 'Gene not found')
@GENES_NS.param('symbol', 'The gene symbol')
class Gene(CMResource):
	'''Return the detailed information of a gene'''
	@GENES_NS.doc('gene')
	@GENES_NS.marshal_with(gene_model)
	def get(self,symbol):
		'''It gets detailed gene information'''
		return self.cmn.gene(symbol)

ROUTES={
	'ns': GENES_NS,
	'path': '/genes',
	'routes': [
		(GeneList,''),
		(Gene,'/<string:symbol>')
	]
}
