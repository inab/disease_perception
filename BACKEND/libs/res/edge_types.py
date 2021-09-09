#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os
from typing import Optional

from .api_models import CMResPath, CMRoutes, CMResource, \
    EDGE_TYPES_NS, simple_edge_type_model, edge_type_model

from .edges import EdgeList
from .nodes import NodeList
from .node_types import NodeType

# Now, the routes
@EDGE_TYPES_NS.response(404, 'Hypergraph not found')
@EDGE_TYPES_NS.param('h_id', 'The hypergraph id')
class EdgeTypeList(CMResource):
	'''Shows a list of all the edge types in a given hypergraph'''
	@EDGE_TYPES_NS.doc('list_edge_types')
	@EDGE_TYPES_NS.marshal_list_with(simple_edge_type_model)
	def get(self, h_id:str):
		'''List all edge types'''
		return self.cmn.edgeTypes(h_id)

@EDGE_TYPES_NS.response(404, 'Hypergraph or edge type not found')
@EDGE_TYPES_NS.param('h_id', 'The hypergraph id')
@EDGE_TYPES_NS.param('e_type', 'The edge type name')
class EdgeType(CMResource):
	'''Return the detailed information of a edge type in the context of a hypergraph'''
	@EDGE_TYPES_NS.doc('edge_type')
	@EDGE_TYPES_NS.marshal_with(edge_type_model)
	def get(self, h_id:str, e_type:Optional[str] = None):
		'''It gets detailed edge type information'''
		res = self.cmn.fetchEdgeType(h_id, e_type)
		for r in res:
			r['edges_link'] = self.api.url_for(EdgeList, h_id=r['h_id'], e_type=r['name'], _external=True)
			r['from_node_type_link'] = self.api.url_for(NodeType, h_id=r['h_id'], n_type=r['from_node_type'], _external=True)
			r['from_nodes_link'] = self.api.url_for(NodeList, h_id=r['h_id'], n_type=r['from_node_type'], _external=True)
			r['to_node_type_link'] = self.api.url_for(NodeType, h_id=r['h_id'], n_type=r['to_node_type'], _external=True)
			r['to_nodes_link'] = self.api.url_for(NodeList, h_id=r['h_id'], n_type=r['to_node_type'], _external=True)
		
		return res  if e_type is None  else  res[0]


ROUTES = CMRoutes(
	ns=EDGE_TYPES_NS,
	path='/h/<string:h_id>/et',
	routes=[
		CMResPath(EdgeTypeList,''),
		CMResPath(EdgeType,'/'),
		CMResPath(EdgeType,'/<string:e_type>'),
	]
)
