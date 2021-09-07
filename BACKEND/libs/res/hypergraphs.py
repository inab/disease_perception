#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResPath, CMRoutes, CMResource, \
    HYPERGRAPHS_NS, hypergraph_model, simple_hypergraph_model

# Now, the routes
#@HYPERGRAPHS_NS.route('',resource_class_kwargs={'cmnetwork': CMNetwork})
class HypergraphList(CMResource):
	'''Shows a list of all the hypergraphs stored'''
	@HYPERGRAPHS_NS.doc('list_hypergraphs')
	@HYPERGRAPHS_NS.marshal_list_with(simple_hypergraph_model)
	def get(self):
		'''List all hypergraphs'''
		#return CMNetwork.genes()
		return self.cmn.hypergraphs()

#@HYPERGRAPHS_NS.route('/<symbol>',resource_class_kwargs={'cmnetwork': CMNetwork})
@HYPERGRAPHS_NS.response(404, 'Hypergraph not found')
@HYPERGRAPHS_NS.param('_id', 'The hypergraph name')
class Hypergraph(CMResource):
	'''Return the detailed information of a hypergraph'''
	@HYPERGRAPHS_NS.doc('_id')
	@HYPERGRAPHS_NS.marshal_with(hypergraph_model)
	def get(self, _id):
		'''It gets detailed information about the hypergraph'''
		return self.cmn.hypergraph(_id)

ROUTES = CMRoutes(
	ns=HYPERGRAPHS_NS,
	path='/h',
	routes=[
		CMResPath(HypergraphList,''),
		CMResPath(Hypergraph,'/<string:_id>')
	]
)
