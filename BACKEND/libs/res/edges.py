#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from typing import Optional

from .api_models import CMResPath, CMRoutes, CMResource, \
    EDGES_NS, simple_edge_model, edge_model

# Now, the routes
@EDGES_NS.response(404, 'Hypergraph or edge type not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
class EdgeList(CMResource):
	'''Shows a list of all the edges in a give hypergraph'''
	@EDGES_NS.doc('list_edges')
	@EDGES_NS.marshal_list_with(simple_edge_model, skip_none=True)
	def get(self, h_id:str, e_type:str):
		'''List all edges'''
		return self.cmn.edges(h_id, e_type)

@EDGES_NS.response(404, 'Hypergraph or edge type or edge not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
@EDGES_NS.param('internal_id', 'The internal edge id')
class EdgeByInternalId(CMResource):
	'''Return the detailed information of an edge given its _id and type'''
	@EDGES_NS.doc('edge')
	@EDGES_NS.marshal_with(edge_model, skip_none=True)
	def get(self, h_id:str, e_type:str, internal_id:int):
		'''It gets detailed edge information'''
		return self.cmn.queryEdge(h_id, e_type, internal_id=internal_id)[0]

@EDGES_NS.response(404, 'Hypergraph or edge type or edge not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
@EDGES_NS.param('_id', 'The edge id')
class EdgeById(CMResource):
	'''Return the detailed information of an edge given its _id and type'''
	@EDGES_NS.doc('edge')
	@EDGES_NS.marshal_with(edge_model, skip_none=True)
	def get(self, h_id:str, e_type:str, _id:str):
		'''It gets detailed edge information'''
		return self.cmn.queryEdge(h_id, e_type, _id=_id)[0]

@EDGES_NS.response(404, 'Hypergraph or edge type not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
class Edges(CMResource):
	'''Return the detailed information of the edges with the same type'''
	@EDGES_NS.doc('list_edges_full')
	@EDGES_NS.marshal_list_with(edge_model, skip_none=True)
	def get(self, h_id:str, e_type:str):
		'''It gets detailed edge information'''
		return self.cmn.queryEdge(h_id, e_type)


ROUTES = CMRoutes(
	ns=EDGES_NS,
	path='/h/<string:h_id>/e/<string:e_type>',
	routes=[
		CMResPath(EdgeList,''),
		CMResPath(Edges,'/'),
		CMResPath(EdgeByInternalId,'/i_id/<int:internal_id>'),
		CMResPath(EdgeById,'/id/<string:_id>'),
	]
)
