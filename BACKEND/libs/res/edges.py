#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from typing import Optional

from .api_models import CMResPath, CMRoutes, CMResource, \
    EDGES_NS, simple_edge_model, edge_model, simple_node_model

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
	@EDGES_NS.doc('edge_by_internal_id')
	@EDGES_NS.marshal_with(edge_model, skip_none=True)
	def get(self, h_id:str, e_type:str, internal_id:int):
		'''It gets detailed edge information'''
		return self.cmn.queryEdge(h_id, e_type, internal_id=internal_id)[0]

@EDGES_NS.response(404, 'Hypergraph or edge type not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
class NodesFromEdges(CMResource):
	@EDGES_NS.doc('nodes_from_edges')
	@EDGES_NS.marshal_list_with(simple_node_model, skip_none=True)
	def get(self, h_id:str, e_type:str):
		'''It gets detailed edge information'''
		return self.cmn.queryEdgeNodes(h_id, e_type, from_to=False)

@EDGES_NS.response(404, 'Hypergraph or edge type not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
class NodesToEdges(CMResource):
	'''Return the detailed information of an edge given its _id and type'''
	@EDGES_NS.doc('nodes_to_edges')
	@EDGES_NS.marshal_list_with(simple_node_model, skip_none=True)
	def get(self, h_id:str, e_type:str):
		'''It gets detailed edge information'''
		return self.cmn.queryEdgeNodes(h_id, e_type, from_to=True)

@EDGES_NS.response(404, 'Hypergraph or edge type or edge not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
@EDGES_NS.param('internal_id', 'The internal edge id')
class NodesFromEdgeByInternalId(CMResource):
	'''Return the detailed information of an edge given its _id and type'''
	@EDGES_NS.doc('nodes_from_edge_by_internal_id')
	@EDGES_NS.marshal_list_with(simple_node_model, skip_none=True)
	def get(self, h_id:str, e_type:str, internal_id:int):
		'''It gets detailed edge information'''
		return self.cmn.queryEdgeNodes(h_id, e_type, from_to=False, internal_id=internal_id)

@EDGES_NS.response(404, 'Hypergraph or edge type or edge not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
@EDGES_NS.param('internal_id', 'The internal edge id')
class NodesToEdgeByInternalId(CMResource):
	'''Return the detailed information of an edge given its _id and type'''
	@EDGES_NS.doc('nodes_to_edge_by_internal_id')
	@EDGES_NS.marshal_list_with(simple_node_model, skip_none=True)
	def get(self, h_id:str, e_type:str, internal_id:int):
		'''It gets detailed edge information'''
		return self.cmn.queryEdgeNodes(h_id, e_type, from_to=True, internal_id=internal_id)

@EDGES_NS.response(404, 'Hypergraph or edge type or edge not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
@EDGES_NS.param('_id', 'The edge id')
class EdgeById(CMResource):
	'''Return the detailed information of an edge given its _id and type'''
	@EDGES_NS.doc('edge_by_id')
	@EDGES_NS.marshal_with(edge_model, skip_none=True)
	def get(self, h_id:str, e_type:str, _id:str):
		'''It gets detailed edge information'''
		return self.cmn.queryEdge(h_id, e_type, _id=_id)[0]

@EDGES_NS.response(404, 'Hypergraph or edge type or edge not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
@EDGES_NS.param('_id', 'The edge id')
class NodesFromEdgeById(CMResource):
	'''Return the detailed information of an edge given its _id and type'''
	@EDGES_NS.doc('nodes_from_edge_by_id')
	@EDGES_NS.marshal_list_with(simple_node_model, skip_none=True)
	def get(self, h_id:str, e_type:str, _id:str):
		'''It gets detailed edge information'''
		return self.cmn.queryEdgeNodes(h_id, e_type, from_to=False, _id=_id)

@EDGES_NS.response(404, 'Hypergraph or edge type or edge not found')
@EDGES_NS.param('h_id', 'The hypergraph id')
@EDGES_NS.param('e_type', 'The edge type name')
@EDGES_NS.param('_id', 'The edge id')
class NodesToEdgeById(CMResource):
	'''Return the detailed information of an edge given its _id and type'''
	@EDGES_NS.doc('nodes_to_edge_by_id')
	@EDGES_NS.marshal_list_with(simple_node_model, skip_none=True)
	def get(self, h_id:str, e_type:str, _id:str):
		'''It gets detailed edge information'''
		return self.cmn.queryEdgeNodes(h_id, e_type, from_to=True, _id=_id)

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
		CMResPath(NodesFromEdges,'/from'),
		CMResPath(NodesToEdges,'/to'),
		CMResPath(EdgeByInternalId,'/i_id/<int:internal_id>'),
		CMResPath(NodesFromEdgeByInternalId,'/i_id/<int:internal_id>/from'),
		CMResPath(NodesToEdgeByInternalId,'/i_id/<int:internal_id>/to'),
		CMResPath(EdgeById,'/id/<string:_id>'),
		CMResPath(NodesFromEdgeById,'/id/<string:_id>/from'),
		CMResPath(NodesToEdgeById,'/id/<string:_id>/to'),
	]
)
