#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from typing import Optional

from .api_models import CMResPath, CMRoutes, CMResource, \
    HYPEREDGES_NS, simple_hyperedge_model, hyperedge_model, \
    simple_node_model

# Now, the routes
@HYPEREDGES_NS.response(404, 'Hypergraph or hyperedge type not found')
@HYPEREDGES_NS.param('h_id', 'The hypergraph id')
@HYPEREDGES_NS.param('he_type', 'The hyperedge type name')
class HyperedgeList(CMResource):
	'''Shows a list of all the hyperedges in a give hypergraph'''
	@HYPEREDGES_NS.doc('list_hyperedges')
	@HYPEREDGES_NS.marshal_list_with(simple_hyperedge_model, skip_none=True)
	def get(self, h_id:str, he_type:str):
		'''List all hyperedges'''
		return self.cmn.hyperedges(h_id, he_type)

@HYPEREDGES_NS.response(404, 'Hypergraph or hyperedge type not found')
@HYPEREDGES_NS.param('h_id', 'The hypergraph id')
@HYPEREDGES_NS.param('he_type', 'The hyperedge type name')
class Hyperedges(CMResource):
	'''Return the detailed information of the hyperedges with the same type'''
	@HYPEREDGES_NS.doc('list_hyperedges_full')
	@HYPEREDGES_NS.marshal_list_with(hyperedge_model, skip_none=True)
	def get(self, h_id:str, he_type:str):
		'''It gets detailed hyperedge information'''
		return self.cmn.queryHyperedge(h_id, he_type)

@HYPEREDGES_NS.response(404, 'Hypergraph or hyperedge type not found')
@HYPEREDGES_NS.param('h_id', 'The hypergraph id')
@HYPEREDGES_NS.param('he_type', 'The hyperedge type name')
class NodesRelHyperedges(CMResource):
	'''Return the detailed information of the hyperedges with the same type'''
	@HYPEREDGES_NS.doc('list_nodes_rel_hyperedges')
	@HYPEREDGES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, he_type:str):
		'''It gets detailed hyperedge information'''
		return self.cmn.queryHyperedgeNodes(h_id, he_type)

@HYPEREDGES_NS.response(404, 'Hypergraph or hyperedge type or hyperedge not found')
@HYPEREDGES_NS.param('h_id', 'The hypergraph id')
@HYPEREDGES_NS.param('he_type', 'The hyperedge type name')
@HYPEREDGES_NS.param('internal_id', 'The internal hyperedge id')
class HyperedgeByInternalId(CMResource):
	'''Return the detailed information of an hyperedge given its _id and type'''
	@HYPEREDGES_NS.doc('hyperedge_by_internal_id')
	@HYPEREDGES_NS.marshal_with(hyperedge_model, skip_none=True)
	def get(self, h_id:str, he_type:str, internal_id:int):
		'''It gets detailed hyperedge information'''
		return self.cmn.queryHyperedge(h_id, he_type, internal_id=internal_id)[0]

@HYPEREDGES_NS.response(404, 'Hypergraph or hyperedge type or hyperedge not found')
@HYPEREDGES_NS.param('h_id', 'The hypergraph id')
@HYPEREDGES_NS.param('he_type', 'The hyperedge type name')
@HYPEREDGES_NS.param('internal_id', 'The internal hyperedge id')
class NodesRelHyperedgeByInternalId(CMResource):
	'''Return the detailed information of an hyperedge given its _id and type'''
	@HYPEREDGES_NS.doc('list_nodes_rel_hyperedge_by_internal_id')
	@HYPEREDGES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, he_type:str, internal_id:int):
		'''It gets detailed hyperedge information'''
		return self.cmn.queryHyperedgeNodes(h_id, he_type, internal_id=internal_id)

@HYPEREDGES_NS.response(404, 'Hypergraph or hyperedge type or hyperedge not found')
@HYPEREDGES_NS.param('h_id', 'The hypergraph id')
@HYPEREDGES_NS.param('he_type', 'The hyperedge type name')
@HYPEREDGES_NS.param('_id', 'The hyperedge id')
class HyperedgeById(CMResource):
	'''Return the detailed information of an hyperedge given its _id and type'''
	@HYPEREDGES_NS.doc('hyperedge_by_id')
	@HYPEREDGES_NS.marshal_with(hyperedge_model, skip_none=True)
	def get(self, h_id:str, he_type:str, _id:str):
		'''It gets detailed hyperedge information'''
		return self.cmn.queryHyperedge(h_id, he_type, _id=_id)[0]

@HYPEREDGES_NS.response(404, 'Hypergraph or hyperedge type or hyperedge not found')
@HYPEREDGES_NS.param('h_id', 'The hypergraph id')
@HYPEREDGES_NS.param('he_type', 'The hyperedge type name')
@HYPEREDGES_NS.param('_id', 'The hyperedge id')
class NodesRelHyperedgeById(CMResource):
	'''Return the detailed information of an hyperedge given its _id and type'''
	@HYPEREDGES_NS.doc('list_nodes_rel_hyperedge_by_id')
	@HYPEREDGES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, he_type:str, _id:str):
		'''It gets detailed hyperedge information'''
		return self.cmn.queryHyperedgeNodes(h_id, he_type, _id=_id)


ROUTES = CMRoutes(
	ns=HYPEREDGES_NS,
	path='/h/<string:h_id>/he/<string:he_type>',
	routes=[
		CMResPath(HyperedgeList,''),
		CMResPath(Hyperedges,'/'),
		CMResPath(NodesRelHyperedges,'/rel'),
		CMResPath(HyperedgeByInternalId,'/i_id/<int:internal_id>'),
		CMResPath(NodesRelHyperedgeByInternalId,'/i_id/<int:internal_id>/rel'),
		CMResPath(HyperedgeById,'/id/<string:_id>'),
		CMResPath(NodesRelHyperedgeById,'/id/<string:_id>/rel'),
	]
)
