#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from typing import Optional

from .api_models import CMResPath, CMRoutes, CMResource, \
    NODES_NS, simple_node_model, node_model

# Now, the routes
#@NODES_NS.route('',resource_class_kwargs={'cmnetwork': CMNetwork})
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('node_type', 'The node type')
class NodeList(CMResource):
	'''Shows a list of all the nodes in a give hypergraph'''
	@NODES_NS.doc('list_nodes')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, node_type:str):
		'''List all nodes'''
		#return CMNetwork.genes()
		return self.cmn.nodes(h_id, node_type)

#@NODES_NS.route('/<symbol>',resource_class_kwargs={'cmnetwork': CMNetwork})
@NODES_NS.response(404, 'Node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('node_type', 'The node type')
@NODES_NS.param('_id', 'The node id')
class NodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('node')
	@NODES_NS.marshal_with(node_model)
	def get(self, h_id:str, node_type:str, _id:str):
		'''It gets detailed node information'''
		return self.cmn.queryNode(h_id, node_type, _id=_id)[0]

#@NODES_NS.route('/<symbol>',resource_class_kwargs={'cmnetwork': CMNetwork})
@NODES_NS.response(404, 'Node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('node_type', 'The node type')
@NODES_NS.param('name', 'The node name')
class NodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_nodes_by_name')
	@NODES_NS.marshal_list_with(node_model)
	def get(self, h_id:str, node_type:str, name:Optional[str] = None):
		'''It gets detailed node information'''
		return self.cmn.queryNode(h_id, node_type, name=name)


ROUTES = CMRoutes(
	ns=NODES_NS,
	path='/h/<string:h_id>/n/<string:node_type>',
	routes=[
		CMResPath(NodeList,''),
		CMResPath(NodesByName,'/'),
		CMResPath(NodesByName,'/name/<string:name>'),
		CMResPath(NodeById,'/id/<string:_id>')
	]
)
