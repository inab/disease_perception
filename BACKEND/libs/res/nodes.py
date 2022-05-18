#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from typing import Optional, List

from .api_models import CMResPath, CMRoutes, CMResource, \
    NODES_NS, simple_node_model, node_model, simple_edge_model, \
    simple_hyperedge_model

# Now, the routes
@NODES_NS.response(404, 'Hypergraph or node type not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
class NodeList(CMResource):
	'''Shows a list of all the nodes in a give hypergraph'''
	@NODES_NS.doc('list_nodes')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str):
		'''List all nodes'''
		#return CMNetwork.genes()
		return self.cmn.nodes(h_id, n_type)

@NODES_NS.response(404, 'Hypergraph or node type not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
class NodesDetailed(CMResource):
	'''Return the detailed information of the nodes with the same type'''
	@NODES_NS.doc('list_nodes_detailed')
	@NODES_NS.marshal_list_with(node_model)
	def get(self, h_id:str, n_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNode(h_id, n_type)

@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('name', 'The node name(s), separated by commas')
class NodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_nodes_by_name')
	@NODES_NS.marshal_list_with(node_model)
	def get(self, h_id:str, n_type:str, name:List[str]):
		'''It gets detailed node information'''
		return self.cmn.queryNode(h_id, n_type, name=name)

@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('internal_id', 'The internal node id(s), separated by commas')
class NodeByInternalId(CMResource):
	'''Return the detailed information of a node given its internal_id and type'''
	@NODES_NS.doc('node')
	@NODES_NS.marshal_list_with(node_model)
	def get(self, h_id:str, n_type:str, internal_id:List[int]):
		'''It gets detailed node information'''
		return self.cmn.queryNode(h_id, n_type, internal_id=internal_id)

@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
class NodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('node')
	@NODES_NS.marshal_list_with(node_model)
	def get(self, h_id:str, n_type:str, _id:str):
		'''It gets detailed node information'''
		return self.cmn.queryNode(h_id, n_type, _id=_id)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('name', 'The node name(s), separated by commas')
class AllEdgesFromNodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_all_edges_from_nodes_by_name')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, name:List[str]):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=False, name=name)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('name', 'The node name(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class EdgesFromNodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_edges_from_nodes_by_name')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, name:List[str], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=False, name=name, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('internal_id', 'The internal node id(s), separated by commas')
class AllEdgesFromNodeByInternalId(CMResource):
	'''Return the detailed information of a node given its internal_id and type'''
	@NODES_NS.doc('list_all_edges_from_node_by_internal_id')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, internal_id:List[int]):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=False, internal_id=internal_id)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('internal_id', 'The internal node id(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class EdgesFromNodeByInternalId(CMResource):
	'''Return the detailed information of a node given its internal_id and type'''
	@NODES_NS.doc('list_edges_from_node_by_internal_id')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, internal_id:List[int], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=False, internal_id=internal_id, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
class AllEdgesFromNodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('list_all_edges_from_node_by_id')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, _id:List[str]):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=False, _id=_id)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class EdgesFromNodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('list_edges_from_node_by_id')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, _id:List[str], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=False, _id=_id, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('name', 'The node name(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class NodesFromNodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_nodes_from_nodes_by_name')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str, name:List[str], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdgesNodes(h_id, n_type, from_to=False, name=name, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('internal_id', 'The internal node id(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class NodesFromNodeByInternalId(CMResource):
	'''Return the detailed information of a node given its internal_id and type'''
	@NODES_NS.doc('list_nodes_from_node_by_internal_id')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str, internal_id:List[int], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdgesNodes(h_id, n_type, from_to=False, internal_id=internal_id, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class NodesFromNodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('list_nodes_from_node_by_id')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str, _id:List[str], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdgesNodes(h_id, n_type, from_to=False, _id=_id, edge_type=e_type)
		
		
@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('name', 'The node name(s), separated by commas')
class AllEdgesToNodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_all_edges_from_nodes_by_name')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, name:List[str]):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=True, name=name)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('name', 'The node name(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class EdgesToNodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_edges_from_nodes_by_name')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, name:List[str], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=True, name=name, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('internal_id', 'The internal node id(s), separated by commas')
class AllEdgesToNodeByInternalId(CMResource):
	'''Return the detailed information of a node given its internal_id and type'''
	@NODES_NS.doc('list_all_edges_from_node_by_internal_id')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, internal_id:List[int]):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=True, internal_id=internal_id)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('internal_id', 'The internal node id(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class EdgesToNodeByInternalId(CMResource):
	'''Return the detailed information of a node given its internal_id and type'''
	@NODES_NS.doc('list_edges_from_node_by_internal_id')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, internal_id:List[int], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=True, internal_id=internal_id, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
class AllEdgesToNodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('list_all_edges_from_node_by_id')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, _id:List[str]):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=True, _id=_id)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class EdgesToNodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('list_edges_from_node_by_id')
	@NODES_NS.marshal_list_with(simple_edge_model)
	def get(self, h_id:str, n_type:str, _id:List[str], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdges(h_id, n_type, from_to=True, _id=_id, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('name', 'The node name(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class NodesToNodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_nodes_to_nodes_by_name')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str, name:List[str], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdgesNodes(h_id, n_type, from_to=True, name=name, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('internal_id', 'The internal node id(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class NodesToNodeByInternalId(CMResource):
	'''Return the detailed information of a node given its internal_id and type'''
	@NODES_NS.doc('list_nodes_to_node_by_internal_id')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str, internal_id:List[int], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdgesNodes(h_id, n_type, from_to=True, internal_id=internal_id, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
@NODES_NS.param('e_type', 'The edge type name')
class NodesToNodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('list_nodes_to_node_by_id')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str, _id:List[str], e_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeEdgesNodes(h_id, n_type, from_to=True, _id=_id, edge_type=e_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('name', 'The node name(s), separated by commas')
class AllHyperedgesRelNodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_all_hyperedges_rel_nodes_by_name')
	@NODES_NS.marshal_list_with(simple_hyperedge_model)
	def get(self, h_id:str, n_type:str, name:List[str]):
		'''It gets detailed node information'''
		return self.cmn.queryNodeHyperedges(h_id, n_type, name=name)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('name', 'The node name(s), separated by commas')
@NODES_NS.param('he_type', 'The hyperedge type name')
class HyperedgesRelNodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_hyperedges_rel_nodes_by_name')
	@NODES_NS.marshal_list_with(simple_hyperedge_model)
	def get(self, h_id:str, n_type:str, name:List[str], he_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeHyperedges(h_id, n_type, name=name, hyperedge_type=he_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('internal_id', 'The internal node id(s), separated by commas')
class AllHyperedgesRelNodeByInternalId(CMResource):
	'''Return the detailed information of a node given its internal_id and type'''
	@NODES_NS.doc('list_all_hyperedges_rel_node_by_internal_id')
	@NODES_NS.marshal_list_with(simple_hyperedge_model)
	def get(self, h_id:str, n_type:str, internal_id:List[int]):
		'''It gets detailed node information'''
		return self.cmn.queryNodeHyperedges(h_id, n_type, internal_id=internal_id)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('internal_id', 'The internal node id(s), separated by commas')
@NODES_NS.param('he_type', 'The hyperedge type name')
class HyperedgesRelNodeByInternalId(CMResource):
	'''Return the detailed information of a node given its internal_id and type'''
	@NODES_NS.doc('list_hyperedges_rel_node_by_internal_id')
	@NODES_NS.marshal_list_with(simple_hyperedge_model)
	def get(self, h_id:str, n_type:str, internal_id:List[int], he_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeHyperedges(h_id, n_type, internal_id=internal_id, hyperedge_type=he_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
class AllHyperedgesRelNodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('list_all_hyperedges_rel_node_by_id')
	@NODES_NS.marshal_list_with(simple_hyperedge_model)
	def get(self, h_id:str, n_type:str, _id:List[str]):
		'''It gets detailed node information'''
		return self.cmn.queryNodeHyperedges(h_id, n_type, _id=_id)

@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
@NODES_NS.param('he_type', 'The hyperedge type name')
class HyperedgesRelNodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('list_hyperedges_rel_node_by_id')
	@NODES_NS.marshal_list_with(simple_hyperedge_model)
	def get(self, h_id:str, n_type:str, _id:List[str], he_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeHyperedges(h_id, n_type, _id=_id, hyperedge_type=he_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('name', 'The node name(s), separated by commas')
@NODES_NS.param('he_type', 'The hyperedge type name')
class NodesRelNodesByName(CMResource):
	'''Return the detailed information of the nodes with the same name and type'''
	@NODES_NS.doc('list_nodes_to_nodes_by_name')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str, name:List[str], he_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeHyperedgesNodes(h_id, n_type, name=name, hyperedge_type=he_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('internal_id', 'The internal node id(s), separated by commas')
@NODES_NS.param('he_type', 'The hyperedge type name')
class NodesRelNodeByInternalId(CMResource):
	'''Return the detailed information of a node given its internal_id and type'''
	@NODES_NS.doc('list_nodes_to_node_by_internal_id')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str, internal_id:List[int], he_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeHyperedgesNodes(h_id, n_type, internal_id=internal_id, hyperedge_type=he_type)

@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
@NODES_NS.param('he_type', 'The hyperedge type name')
class NodesRelNodeById(CMResource):
	'''Return the detailed information of a node given its _id and type'''
	@NODES_NS.doc('list_nodes_to_node_by_id')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str, _id:List[str], he_type:str):
		'''It gets detailed node information'''
		return self.cmn.queryNodeHyperedgesNodes(h_id, n_type, _id=_id, hyperedge_type=he_type)


@NODES_NS.response(404, 'Hypergraph or node type or node not found')
@NODES_NS.param('h_id', 'The hypergraph id')
@NODES_NS.param('n_type', 'The node type name')
@NODES_NS.param('_id', 'The node id(s), separated by commas')
@NODES_NS.param('edges_connection', 'The edges to connect nodes, separated by commas')
class NodesFromUpperNodes(CMResource):
	'''Return the nodes type from upper nodes ids'''
	@NODES_NS.doc('list_nodes_to_node_by_id')
	@NODES_NS.marshal_list_with(simple_node_model)
	def get(self, h_id:str, n_type:str, _id:List[str], edges_connection:List[str]):
		'''It gets detailed node information'''
		return self.cmn.queryNodeFromUpperNodes(h_id, n_type, _id, edges_connection)



ROUTES = CMRoutes(
	ns=NODES_NS,
	path='/h/<string:h_id>/n/<string:n_type>',
	routes=[
		CMResPath(NodeList,''),
		CMResPath(NodesDetailed,'/'),
		
		CMResPath(NodesByName,'/name/<list(string,sep=","):name>'),
		CMResPath(NodeByInternalId,'/i_id/<list(int,sep=","):internal_id>'),
		CMResPath(NodeById,'/id/<string:_id>'),
		
		CMResPath(AllEdgesFromNodesByName,'/name/<list(string,sep=","):name>/from/e'),
		CMResPath(EdgesFromNodesByName,'/name/<list(string,sep=","):name>/from/e/<string:e_type>'),
		CMResPath(AllEdgesFromNodeByInternalId,'/i_id/<list(int,sep=","):internal_id>/from/e'),
		CMResPath(EdgesFromNodeByInternalId,'/i_id/<list(int,sep=","):internal_id>/from/e/<string:e_type>'),
		CMResPath(AllEdgesFromNodeById,'/id/<list(string,sep=","):_id>/from/e'),
		CMResPath(EdgesFromNodeById,'/id/<list(string,sep=","):_id>/from/e/<string:e_type>'),
		
		CMResPath(NodesFromNodesByName,'/name/<list(string,sep=","):name>/from/e/<string:e_type>/n'),
		CMResPath(NodesFromNodeByInternalId,'/i_id/<list(int,sep=","):internal_id>/from/e/<string:e_type>/n'),
		CMResPath(NodesFromNodeById,'/id/<list(string,sep=","):_id>/from/e/<string:e_type>/n'),
		
		CMResPath(AllEdgesToNodesByName,'/name/<list(string,sep=","):name>/to/e'),
		CMResPath(EdgesToNodesByName,'/name/<list(string,sep=","):name>/to/e/<string:e_type>'),
		CMResPath(AllEdgesToNodeByInternalId,'/i_id/<list(int,sep=","):internal_id>/to/e'),
		CMResPath(EdgesToNodeByInternalId,'/i_id/<list(int,sep=","):internal_id>/to/e/<string:e_type>'),
		CMResPath(AllEdgesToNodeById,'/id/<list(string,sep=","):_id>/to/e'),
		CMResPath(EdgesToNodeById,'/id/<list(string,sep=","):_id>/to/e/<string:e_type>'),
		
		CMResPath(NodesToNodesByName,'/name/<list(string,sep=","):name>/to/e/<string:e_type>/n'),
		CMResPath(NodesToNodeByInternalId,'/i_id/<list(int,sep=","):internal_id>/to/e/<string:e_type>/n'),
		CMResPath(NodesToNodeById,'/id/<list(string,sep=","):_id>/to/e/<string:e_type>/n'),
		
		CMResPath(AllHyperedgesRelNodesByName,'/name/<list(string,sep=","):name>/he'),
		CMResPath(HyperedgesRelNodesByName,'/name/<list(string,sep=","):name>/he/<string:he_type>'),
		CMResPath(AllHyperedgesRelNodeByInternalId,'/i_id/<list(int,sep=","):internal_id>/he'),
		CMResPath(HyperedgesRelNodeByInternalId,'/i_id/<list(int,sep=","):internal_id>/he/<string:he_type>'),
		CMResPath(AllHyperedgesRelNodeById,'/id/<list(string,sep=","):_id>/he'),
		CMResPath(HyperedgesRelNodeById,'/id/<list(string,sep=","):_id>/he/<string:he_type>'),
		
		CMResPath(NodesRelNodesByName,'/name/<list(string,sep=","):name>/he/<string:he_type>/n'),
		CMResPath(NodesRelNodeByInternalId,'/i_id/<list(int,sep=","):internal_id>/he/<string:he_type>/n'),
		CMResPath(NodesRelNodeById,'/id/<list(string,sep=","):_id>/he/<string:he_type>/n'),

		CMResPath(NodesFromUpperNodes,'/to/n/id/<list(string,sep=","):_id>/e/<list(string,sep=","):edges_connection>')
	]
)
