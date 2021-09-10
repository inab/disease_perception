#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os
from typing import Optional

from .api_models import CMResPath, CMRoutes, CMResource, \
    HYPEREDGE_TYPES_NS, simple_hyperedge_type_model, hyperedge_type_model

from .hyperedges import HyperedgeList
from .nodes import NodeList
from .node_types import NodeType

# Now, the routes
@HYPEREDGE_TYPES_NS.response(404, 'Hypergraph not found')
@HYPEREDGE_TYPES_NS.param('h_id', 'The hypergraph id')
class HyperedgeTypeList(CMResource):
	'''Shows a list of all the hyperedge types in a given hypergraph'''
	@HYPEREDGE_TYPES_NS.doc('list_hyperedge_types')
	@HYPEREDGE_TYPES_NS.marshal_list_with(simple_hyperedge_type_model)
	def get(self, h_id:str):
		'''List all edge types'''
		return self.cmn.hyperedgeTypes(h_id)

@HYPEREDGE_TYPES_NS.response(404, 'Hypergraph or edge type not found')
@HYPEREDGE_TYPES_NS.param('h_id', 'The hypergraph id')
@HYPEREDGE_TYPES_NS.param('he_type', 'The edge type name')
class HyperedgeType(CMResource):
	'''Return the detailed information of a hyperedge type in the context of a hypergraph'''
	@HYPEREDGE_TYPES_NS.doc('hyperedge_type')
	@HYPEREDGE_TYPES_NS.marshal_with(hyperedge_type_model)
	def get(self, h_id:str, he_type:Optional[str] = None):
		'''It gets detailed hyperedge type information'''
		res = self.cmn.fetchHyperedgeType(h_id, he_type)
		for r in res:
			r['hyperedges_link'] = self.api.url_for(HyperedgeList, h_id=r['h_id'], he_type=r['name'], _external=True)
			r['node_type_links'] = list(map(lambda nt: self.api.url_for(NodeType, h_id=r['h_id'], n_type=nt, _external=True), r['node_types']))
			r['node_links'] = list(map(lambda nt: self.api.url_for(NodeList, h_id=r['h_id'], n_type=nt, _external=True), r['node_types']))
			#r['from_node_type_link'] = self.api.url_for(NodeType, h_id=r['h_id'], n_type=r['from_node_type'], _external=True)
			#r['from_nodes_link'] = self.api.url_for(NodeList, h_id=r['h_id'], n_type=r['from_node_type'], _external=True)
			#r['to_node_type_link'] = self.api.url_for(NodeType, h_id=r['h_id'], n_type=r['to_node_type'], _external=True)
			#r['to_nodes_link'] = self.api.url_for(NodeList, h_id=r['h_id'], n_type=r['to_node_type'], _external=True)
		
		return res  if he_type is None  else  res[0]


ROUTES = CMRoutes(
	ns=HYPEREDGE_TYPES_NS,
	path='/h/<string:h_id>/het',
	routes=[
		CMResPath(HyperedgeTypeList,''),
		CMResPath(HyperedgeType,'/'),
		CMResPath(HyperedgeType,'/<string:he_type>'),
	]
)
