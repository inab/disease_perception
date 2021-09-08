#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResPath, CMRoutes, CMResource, \
    NODE_TYPES_NS, simple_node_type_model, node_type_model

from .nodes import NodeList

# Now, the routes
@NODE_TYPES_NS.param('h_id', 'The hypergraph id')
class NodeTypeList(CMResource):
	'''Shows a list of all the nodes in a give hypergraph'''
	@NODE_TYPES_NS.doc('list_node_types')
	@NODE_TYPES_NS.marshal_list_with(simple_node_type_model)
	def get(self, h_id:str):
		'''List all node types'''
		return self.cmn.nodeTypes(h_id)

@NODE_TYPES_NS.response(404, 'Node type not found')
@NODE_TYPES_NS.param('h_id', 'The hypergraph id')
@NODE_TYPES_NS.param('node_type', 'The node type')
class NodeType(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODE_TYPES_NS.doc('node_type')
	@NODE_TYPES_NS.marshal_list_with(node_type_model)
	def get(self, h_id:str, node_type:str = None):
		'''It gets detailed node type information'''
		res = self.cmn.fetchNodeType(h_id, node_type)
		for r in res:
			print(self.api.url_for(NodeList, h_id=r['h_id'], node_type=r['name'], _external=True), file=sys.stderr)
			r['nodes_link'] = self.api.url_for(NodeList, h_id=r['h_id'], node_type=r['name'], _external=True)
		
		return res


ROUTES = CMRoutes(
	ns=NODE_TYPES_NS,
	path='/h/<string:h_id>/nt',
	routes=[
		CMResPath(NodeTypeList,''),
		CMResPath(NodeType,'/'),
		CMResPath(NodeType,'/<string:node_type>'),
	]
)
