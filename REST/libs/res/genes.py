#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask_restplus import Namespace, Resource

from .api_models import *

genes_ns = Namespace('genes','Comorbidities related genes')

# Now, the routes
#@genes_ns.route('',resource_class_kwargs={'cmnetwork': CMNetwork})
class GeneList(CMResource):
	'''Shows a list of all the genes related in comorbidities'''
	@genes_ns.doc('list_genes')
	@genes_ns.marshal_list_with(simple_gene_model)
	def get(self):
		'''List all genes'''
		#return CMNetwork.genes()
		return self.cmn.genes()

#@genes_ns.route('/<symbol>',resource_class_kwargs={'cmnetwork': CMNetwork})
@genes_ns.response(404, 'Gene not found')
@genes_ns.param('symbol', 'The gene symbol')
class Gene(CMResource):
	'''Return the detailed information of a gene'''
	@genes_ns.doc('gene')
	@genes_ns.marshal_with(gene_model)
	def get(self,symbol):
		'''It gets detailed gene information'''
		return self.cmn.gene(symbol)
