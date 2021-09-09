#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os
import copy

from flask_restplus import Namespace, Api, Resource, fields
from typing import List, NamedTuple, Union

class CMResource(Resource):
	'''This class eases passing the instance of the comorbidity network query API'''
	def __init__(self,api=None,*args,**kwargs):
		super().__init__(api,*args,**kwargs)
		self.cmn = kwargs['cmnetwork']



NS = Namespace('cm','Comorbidities network info')
#ns = api.namespace('cm', description='Comorbidities network queries')

class CMResPath(NamedTuple):
	"""
	Definition of the resource and its relative paths
	"""
	res: Resource
	paths: Union[str,List[str]]

class CMRoutes(NamedTuple):
	"""
	Definition of the routes of all the resources with a common path
	"""
	ns: Namespace
	path: str
	routes: List[CMResPath]

########################
# The different models #
########################
HYPERGRAPHS_NS = Namespace('hypergraphs','Stored hypergraphs')

simple_hypergraph_schema = {
	'properties': {
		'_id': {
			'type': 'string',
			'description': 'The hypergraph id'
		},
		'stored_at': {
			'type': 'string',
			'description': 'When this hypergraph was stored',
			'format': 'date-time'
		},
		'updated_at': {
			'type': 'string',
			'description': 'When this hypergraph was updated',
			'format': 'date-time'
		}
	},
	'type': 'object',
	'required': [ '_id', 'stored_at' ]
}

simple_hypergraph_model = HYPERGRAPHS_NS.model('SimpleHypergraph', {
	'_id': fields.String(required=True, description=simple_hypergraph_schema['properties']['_id']['description']),
	'stored_at': fields.DateTime(required=True, description=simple_hypergraph_schema['properties']['stored_at']['description']),
	'updated_at': fields.DateTime(required=True, description=simple_hypergraph_schema['properties']['updated_at']['description']),
})

simple_hypergraph_model_schema = HYPERGRAPHS_NS.schema_model('SimpleHypergraph', simple_hypergraph_schema)

hypergraph_schema = {
	"$id": "http://disease-perception.bsc.es/schemas/1.0/hypergraph_types/hypergraph",
	"$schema": "http://json-schema.org/draft-07/schema#",
	"type": "object",
	"properties": {
		"_schema": {
			"type": "string",
			"const": "http://disease-perception.bsc.es/schemas/1.0/hypergraph_types/hypergraph"
		},
		"_id": {
			"type": "string",
			"minLength": 1
		},
		"_generated": {
			"title": "Official date when this dataset was generated",
			"type": "string",
			"format": "date-time"
		},
		"name": {
			"title": "Short name of this hypergraph",
			"type": "string",
			"minLength": 1,
			"maxLength": 256
		},
		"description": {
			"title": "A description",
			"description": "A detailed description of this hypergraph, in Markdown",
			"type": "string"
		},
		"attributions": {
			"type": "array",
			"items": {
				"type": "object",
				"properties": {
					"name": {
						"title": "The name of the contributor",
						"type": "string"
					},
					"roles": {
						"title": "The different roles of this attribution",
						"type": "array",
						"items": {
							"type": "string",
							"description": "The valid roles come from CASRAI CRediT, and can be visited through http://credit.niso.org/contributor-roles/{term}/",
							"enum": [
								"conceptualization",
								"data-curation",
								"formal-analysis",
								"funding-acquisition",
								"investigation",
								"methodology",
								"project-administration",
								"resources",
								"software",
								"supervision",
								"validation",
								"visualization",
								"writing-original-draft",
								"writing-review-editing"
							]
						},
						"uniqueItems": True
					},
					"pid": {
						"title": "A public, unique id of the contributor. Accepted ones are ORCID or ISNI ids",
						"type": "string",
						"pattern": "^orcid:[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]|isni:[0-9]{15}[0-9X]{1}$"
					}
				},
				"required": [
					"name",
					"pid"
				]
			},
			"uniqueItems": True
		},
		"licence": {
			"title": "The hypergraph data distribution licence",
			"type": "string",
			"format": "uri"
		},
		"pids": {
			"type": "array",
			"items": {
				"type": "object",
				"properties": {
					"ns": {
						"title": "Namespace (or prefix) of the permanent id",
						"type": "string",
						"examples": [
							"doi"
						]
					},
					"pid": {
						"title": "A valid persistent id declared in the namespace",
						"type": "string"
					}
				},
				"required": [
					"ns",
					"pid"
				]
			}
		},
		"properties": {
			"title": "Various properties",
			"type": "object"
		}
	},
	"required": [
		"_id",
		"_schema",
		"_generated",
		"name",
		"attributions",
		"licence"
	]
}
h_s_props = hypergraph_schema['properties']

complete_hypergraph_schema = copy.deepcopy(simple_hypergraph_schema)
complete_hypergraph_schema['properties']['payload'] = hypergraph_schema

h_attribution_model = HYPERGRAPHS_NS.model('Attribution', {
	'name': fields.String(required=True, description=h_s_props['attributions']['items']['properties']['name']['title']),
	'roles': fields.List(fields.String, description=h_s_props['attributions']['items']['properties']['roles']['title']),
	'pid': fields.String(required=True, description=h_s_props['attributions']['items']['properties']['pid']['title']),
})

pid_model = HYPERGRAPHS_NS.model('PID', {
	'ns':  fields.String(required=True, description=h_s_props['pids']['items']['properties']['ns']['title']),
	'pid':  fields.String(required=True, description=h_s_props['pids']['items']['properties']['pid']['title']),
})

embedded_hypergraph_model = HYPERGRAPHS_NS.model('HypergraphPayload', {
	'_schema': fields.String(required=True, default=h_s_props['_schema']['const']),
	'_id': fields.String(required=True),
	'_generated': fields.DateTime(required=True, description=h_s_props['_generated']['title']),
	'name': fields.String(required=True, description=h_s_props['name']['title']),
	'description': fields.String(description=h_s_props['description']['title']),
	'attributions': fields.List(fields.Nested(h_attribution_model), required=True),
	'licence': fields.String(required=True, description=h_s_props['licence']['title']),
	'pids': fields.List(fields.Nested(pid_model)),
	'properties': fields.Raw(description=h_s_props['properties']['title']),
})

hypergraph_model = HYPERGRAPHS_NS.model('Hypergraph', {
	'_id': fields.String(required=True, description=simple_hypergraph_schema['properties']['_id']['description']),
	'stored_at': fields.DateTime(required=True, description=simple_hypergraph_schema['properties']['stored_at']['description']),
	'updated_at': fields.DateTime(required=True, description=simple_hypergraph_schema['properties']['updated_at']['description']),
	'payload': fields.Nested(embedded_hypergraph_model),
})

# This content is already available in the repo
hypergraph_model_schema = HYPERGRAPHS_NS.schema_model('Hypergraph', complete_hypergraph_schema)


NODES_NS = Namespace('nodes','Hypergraph nodes')

simple_node_model = NODES_NS.model('SimpleNode', {
	'_id': fields.String(required=True, description='The id of this node as a hypergraph node'),
	'_type': fields.String(required=True, description='The type of the node'),
	'internal_id': fields.Integer(required=True, description='The internal id of this node as a hypergraph node. This value can change from one load to another in the database'),
	'h_id': fields.String(required=True, description='The id of the hypergraph where the node is'),
	'name': fields.String(required=True,description = 'The name of the node'),
})

simple_node_schema = {
	'properties': {
		'_id': {
			'type': 'string',
			'description': 'The id of this node as a hypergraph node'
		},
		'_type': {
			'type': 'string',
			'description': 'The type of the node'
		},
		'internal_id': {
			'type': 'integer',
			'description': 'The internal id of this node as a hypergraph node. This value can change from one load to another in the database'
		},
		'h_id': {
			'type': 'string',
			'description': 'The hypergraph id where the _id makes sense'
		},
		'name': {
			'type': 'string',
			'description': 'The name of the node'
		}
	},
	'type': 'object',
	'required': [ '_id', '_type', 'internal_id', 'h_id', 'name' ]
}

simple_node_model_schema = NODES_NS.schema_model('SimpleNode', simple_node_schema)

node_schema = {
	"$id": "http://disease-perception.bsc.es/schemas/1.0/node_types/node",
	"$schema": "http://json-schema.org/draft-07/schema#",
	"type": "object",
	"properties": {
		"_schema": {
			"type": "string",
			"default": "http://disease-perception.bsc.es/schemas/1.0/node_types/node"
		},
		"_id": {
			"type": "string"
		},
		"name": {
			"type": "string"
		},
		"pids": {
			"type": "array",
			"items": {
				"type": "object",
				"properties": {
					"ns": {
						"title": "Namespace (or prefix) of the permanent id",
						"type": "string",
						"examples": [
							"icd9",
							"icd10"
						]
					},
					"pid": {
						"title": "A valid persistent id declared in the namespace",
						"type": "string"
					}
				},
				"required": [
					"ns",
					"pid"
				]
			}
		},
		"properties": {
			"title": "Various properties",
			"type": "object"
		}
	},
	"required": [
		"_id",
		"name"
	]
}

n_s_props = node_schema['properties']

complete_node_schema = copy.deepcopy(simple_node_schema)
complete_node_schema['properties']['payload'] = node_schema

embedded_node_model = NODES_NS.model('NodePayload', {
	'_schema': fields.String(required=True, default=n_s_props['_schema']['default']),
	'_id': fields.String(required=True),
	'name': fields.String(required=True),
	'pids': fields.List(fields.Nested(pid_model)),
	'properties': fields.Raw(description=n_s_props['properties']['title']),
})

node_model = NODES_NS.model('Node', {
	'_id': fields.String(required=True, description='The id of this node as a hypergraph node'),
	'_type': fields.String(required=True, description='The type of the node'),
	'h_id': fields.String(required=True, description='The id of the hypergraph where the node is'),
	'internal_id': fields.Integer(required=True, description='The internal id of this node as a hypergraph node. This value can change from one load to another in the database'),
	'name': fields.String(required=True,description = 'The name of the node'),
	'payload': fields.Nested(embedded_node_model),
})

node_model_schema = NODES_NS.schema_model('Node', complete_node_schema)


NODE_TYPES_NS = Namespace('node_types','Hypergraph\'s node types')

simple_node_type_schema = {
	'properties': {
		'name': {
			'type': 'string',
			'description': 'The name of the node type'
		},
		'h_id': {
			'type': 'string',
			'description': 'The hypergraph id where there is at least a node of this type'
		},
		'schema_id': {
			'type': 'string',
			'description': 'The URI of the JSON Schemas used to model payloads for nodes of this type'
		}
	},
	'type': 'object',
	'required': [ 'name', 'h_id', 'schema_id' ]
}

simple_node_type_model = NODE_TYPES_NS.model('SimpleNodeType', {
	'name': fields.String(required=True, description=simple_node_type_schema['properties']['name']['description']),
	'h_id': fields.String(required=True, description='The id of the hypergraph where the node is'),
	'schema_id': fields.String(required=True, description=simple_node_type_schema['properties']['schema_id']['description']),
})

simple_node_type_model_schema = NODE_TYPES_NS.schema_model('SimpleNodeType', simple_node_type_schema)

node_type_schema = {
	'properties': {
		'name': {
			'type': 'string',
			'description': 'The name of the node type'
		},
		'h_id': {
			'type': 'string',
			'description': 'The hypergraph id where there is at least a node of this type'
		},
		'schema_id': {
			'type': 'string',
			'description': 'The URI of the JSON Schemas used to model payloads for nodes of this type'
		},
		'number': {
			'type': 'integer',
			'description': 'Number of nodes of this type in this hypergraph',
			'minimum': 1
		},
		'nodes_link': {
			'type': 'string',
			'description': 'The link to the REST resource with the nodes',
			'format': 'uri'
		},
		'description': {
			'type': 'string',
			'description': 'An optional description'
		},
		'payload': {
			'description': 'The optional payload of the node type'
		}
	},
	'type': 'object',
	'required': [ 'name', 'h_id', 'schema_id' ]
}

nt_s_props = node_type_schema['properties']

node_type_model = NODE_TYPES_NS.model('NodeType', {
	'name': fields.String(required=True, description=nt_s_props['name']['description']),
	'h_id': fields.String(required=True, description='The id of the hypergraph where the node is'),
	'schema_id': fields.String(required=True, description=nt_s_props['schema_id']['description']),
	'number': fields.Integer(required=True, description=nt_s_props['number']['description']),
	'nodes_link': fields.Raw(required=True),
	'description': fields.String(description=nt_s_props['description']['description']),
	'payload': fields.Raw(description=nt_s_props['payload']['description']),
})

node_type_model_schema = NODE_TYPES_NS.schema_model('NodeType', node_type_schema)





EDGES_NS = Namespace('edges','Hypergraph edges')

simple_edge_model = EDGES_NS.model('SimpleEdge', {
	'_id': fields.String(required=True, description='The id of this edge as a hypergraph edge'),
	'_type': fields.String(required=True, description='The type of the edge'),
	'internal_id': fields.Integer(required=True, description='The internal id of this edge as a hypergraph edge. This value can change from one load to another in the database'),
	'h_id': fields.String(required=True, description='The id of the hypergraph where the edge is'),
	'weight': fields.Float(description='The weight of the edge'),
	'f_id': fields.String(required=True, description='The id of the node where this edge starts'),
	't_id': fields.String(required=True, description='The id of the node where this edge ends'),
	'f_internal_id': fields.Integer(required=True, description='The internal id of the node where this edge starts'),
	't_internal_id': fields.Integer(required=True, description='The internal id of the node where this edge ends'),
})

simple_edge_schema = {
	'properties': {
		'_id': {
			'type': 'string',
			'description': 'The optional id of this edge as a hypergraph edge'
		},
		'_type': {
			'type': 'string',
			'description': 'The type of the edge'
		},
		'internal_id': {
			'type': 'integer',
			'description': 'The internal id of this edge as a hypergraph edge. This value can change from one load to another in the database'
		},
		'h_id': {
			'type': 'string',
			'description': 'The hypergraph id where the edge was declared'
		},
		'f_id': {
			'type': 'string',
			'description': 'The id of the node where this edge starts'
		},
		't_id': {
			'type': 'string',
			'description': 'The id of the node where this edge ends'
		},
		'weight': {
			'type': 'number',
			'description': 'The weight of the edge'
		},
		'f_internal_id': {
			'type': 'integer',
			'description': 'The internal id of the node where this edge starts'
		},
		't_internal_id': {
			'type': 'integer',
			'description': 'The internal id of the node where this edge ends'
		},
	},
	'type': 'object',
	'required': [ 'internal_id', '_id', '_type', 'h_id', 'f_id', 't_id', 'f_internal_id', 't_internal_id' ]
}

simple_edge_model_schema = EDGES_NS.schema_model('SimpleEdge', simple_edge_schema)

complete_edge_schema = copy.deepcopy(simple_edge_schema)
complete_edge_schema['properties'].update({
	'payload': {
		'description': 'The optional payload'
	}
})

wce = fields.Wildcard(fields.Raw)
edge_model = EDGES_NS.model('Edge', {
	'_id': fields.String(required=True, description='The id of this edge as a hypergraph edge'),
	'_type': fields.String(required=True, description='The type of the edge'),
	'internal_id': fields.Integer(required=True, description='The internal id of this edge as a hypergraph edge. This value can change from one load to another in the database'),
	'h_id': fields.String(required=True, description='The id of the hypergraph where the edge is'),
	'weight': fields.Float(skip_none=True, description='The weight of the edge'),
	'f_id': fields.String(required=True, description='The id of the node where this edge starts'),
	't_id': fields.String(required=True, description='The id of the node where this edge ends'),
	'f_internal_id': fields.Integer(required=True, description='The internal id of the node where this edge starts'),
	't_internal_id': fields.Integer(required=True, description='The internal id of the node where this edge ends'),
#	'payload': {
#		'*': wce,
#	},
	'payload': fields.Raw(description='The optional payload'),
})

edge_model_schema = EDGES_NS.schema_model('Edge', complete_edge_schema)


EDGE_TYPES_NS = Namespace('edge_types','Hypergraph\'s edge types')

simple_edge_type_schema = {
	'properties': {
		'name': {
			'type': 'string',
			'description': 'The name of the edge type'
		},
		'h_id': {
			'type': 'string',
			'description': 'The hypergraph id where there is at least a edge of this type'
		},
		'schema_id': {
			'type': 'string',
			'description': 'The URI of the JSON Schemas used to model payloads for edges of this type'
		}
	},
	'type': 'object',
	'required': [ 'name', 'h_id', 'schema_id' ]
}

simple_edge_type_model = EDGE_TYPES_NS.model('SimpleEdgeType', {
	'name': fields.String(required=True, description=simple_edge_type_schema['properties']['name']['description']),
	'h_id': fields.String(required=True, description='The id of the hypergraph where the edge is'),
	'schema_id': fields.String(required=True, description=simple_edge_type_schema['properties']['schema_id']['description']),
})

simple_edge_type_model_schema = EDGE_TYPES_NS.schema_model('SimpleEdgeType', simple_edge_type_schema)

edge_type_schema = {
	'properties': {
		'name': {
			'type': 'string',
			'description': 'The name of the edge type'
		},
		'h_id': {
			'type': 'string',
			'description': 'The hypergraph id where there is at least a edge of this type'
		},
		'schema_id': {
			'type': 'string',
			'description': 'The URI of the JSON Schemas used to model payloads for edges of this type'
		},
		'weight_name': {
			'type': 'string',
			'description': 'The name of the weights used for edges of this type'
		},
		'weight_desc': {
			'type': 'string',
			'description': 'The description of the weights used for edges of this type'
		},
		'number': {
			'type': 'integer',
			'description': 'Number of edges of this type in this hypergraph',
			'minimum': 1
		},
		'edges_link': {
			'type': 'string',
			'description': 'The link to the REST resource with the edges',
			'format': 'uri'
		},
		'from_node_type': {
			'type': 'string',
			'description': 'The node type origin of all the edges of this type'
		},
		'from_node_type_link': {
			'type': 'string',
			'description': 'The link to the REST resource of the origin node type',
			'format': 'uri'
		},
		'from_nodes_link': {
			'type': 'string',
			'description': 'The link to the REST resource of the origin nodes',
			'format': 'uri'
		},
		'to_node_type': {
			'type': 'string',
			'description': 'The node type destination of all the edges of this type'
		},
		'to_node_type_link': {
			'type': 'string',
			'description': 'The link to the REST resource of the destination node type',
			'format': 'uri'
		},
		'to_nodes_link': {
			'type': 'string',
			'description': 'The link to the REST resource of the destination nodes',
			'format': 'uri'
		},
		'description': {
			'type': 'string',
			'description': 'An optional description'
		},
		'payload': {
			'description': 'The optional payload of the edge type'
		}
	},
	'type': 'object',
	'required': [ 'name', 'h_id', 'schema_id' ]
}

et_s_props = edge_type_schema['properties']

edge_type_model = EDGE_TYPES_NS.model('EdgeType', {
	'name': fields.String(required=True, description=et_s_props['name']['description']),
	'h_id': fields.String(required=True, description='The id of the hypergraph where the edge is'),
	'schema_id': fields.String(required=True, description=et_s_props['schema_id']['description']),
	'weight_name': fields.String(description=et_s_props['weight_name']['description']),
	'weight_desc': fields.String(description=et_s_props['weight_desc']['description']),
	'number': fields.Integer(required=True, description=et_s_props['number']['description']),
	'edges_link': fields.Raw(required=True),
	'from_node_type': fields.String(required=True, description=et_s_props['from_node_type']['description']),
	'from_node_type_link': fields.Raw(required=True),
	'from_nodes_link': fields.Raw(required=True),
	'to_node_type': fields.String(required=True, description=et_s_props['to_node_type']['description']),
	'to_node_type_link': fields.Raw(required=True),
	'to_nodes_link': fields.Raw(required=True),
	'description': fields.String(description=et_s_props['description']['description']),
	'payload': fields.Raw(description=et_s_props['payload']['description']),
})

edge_type_model_schema = EDGE_TYPES_NS.schema_model('EdgeType', edge_type_schema)







GENES_NS = Namespace('genes','Comorbidities related genes')

simple_gene_model = GENES_NS.model('SimpleGene', {
	'symbol': fields.String(required=True,description = 'The gene symbol'),
})

simple_gene_model_schema = GENES_NS.schema_model('SimpleGene', {
	'properties': {
		'symbol': {
			'type': 'string',
			'description': 'The gene symbol'
		}
	},
	'type': 'object',
	'required': [ 'symbol' ]
})

gene_model = GENES_NS.model('Gene', {
	'symbol': fields.String(required=True,description = 'The gene symbol'),
	'ensembl_id': fields.String(description = 'The EnsEMBL gene id'),
	'uniprot_acc': fields.String(description = 'The UniProt Accession Number')
})

gene_model_schema = GENES_NS.schema_model('Gene', {
	'properties': {
		'symbol': {
			'type': 'string',
			'description': 'The gene symbol'
		},
		'ensembl_id': {
			'type': 'string',
			'pattern': '^ENSG[0-9]{11}$',
			'description': 'The EnsEMBL gene id'
		},
		'uniprot_acc': {
			'type': 'string',
			'description': 'The UniProt Accession Number'
		}
	},
	'type': 'object',
	'required': [ 'symbol' ]
})


DRUGS_NS = Namespace('drugs','Comorbidities related drugs')

drug_model = DRUGS_NS.model('Drug', {
	'id': fields.Integer(required=True, description = 'The internal id of the drug'),
	'name': fields.String(required=True, description = 'The drug name')
})

drug_model_schema = DRUGS_NS.schema_model('Drug', {
	'description': 'A drug stored in the comorbidities database',
	'properties': {
		'id': {
			'type': 'integer',
			'description': 'The internal id of the drug'
		},
		'name': {
			'type': 'string',
			'description': 'The drug name'
		}
	},
	'type': 'object',
	'required': ['id','name']
})

simple_drug_model = drug_model
simple_drug_model_schema = drug_model_schema


STUDIES_NS = Namespace('studies','Comorbidities related studies')

study_model = STUDIES_NS.model('Study', {
	'id': fields.String(required=True, description = 'The id of the study in the original source'),
	'source': fields.String(required=True, description = 'The study source')
})

study_model_schema = STUDIES_NS.schema_model('Study', {
	'description': 'A study stored in the comorbidities database',
	'properties': {
		'id': {
			'type': 'string',
			'description': 'The id of the study in the original source'
		},
		'source': {
			'type': 'string',
			'description': 'The study source',
			'enum': [ 'GEO', 'ArrayExpress' ]
		}
	},
	'type': 'object',
	'required': ['id','source']
})

simple_study_model = study_model
simple_study_model_schema = study_model_schema

DISEASE_NS = Namespace('diseases','Diseases')

simple_disease_model = DISEASE_NS.model('SimpleDisease', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease'),
	'disease_group_id': fields.Integer(required=True, description = 'The internal id of the disease group where this disease is classified into'),
	'name': fields.String(required=True, description = 'The disease symbolic name')
})

disease_model = DISEASE_NS.model('Disease', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease'),
	'disease_group_id': fields.Integer(required=True, description = 'The internal id of the disease group where this disease is classified into'),
	'name': fields.String(required=True, description = 'The disease symbolic name'),
	'color': fields.String(required=True, description = 'Preferred color for this group of diseases'),
	'icd9': fields.String(description = 'The ICD9 code of this disease'),
	'icd10': fields.String(description = 'The ICD10 code of this disease')
})

disease_comorbidity_model = DISEASE_NS.model('DiseaseComorbidity', {
	'from_id': fields.Integer(required=True, description = 'The internal id of the disease A (from)'),
	'to_id': fields.Integer(required=True, description = 'The internal id of the disease B (to)'),
	'rel_risk': fields.Float(required=True, description = 'The relative risk of comorbidity')
})

disease_patient_subgroup_comorbidity_model = DISEASE_NS.model('DiseasePatientSubgroupComorbidity', {
	'from_id': fields.Integer(required=True, description = 'The internal id of the patient subgroup A (from)'),
	'from_size': fields.Integer(required=True, description = 'The size of the patient subgroup A (from)'),
	'to_id': fields.Integer(required=True, description = 'The internal id of the patient subgroup B (to)'),
	'to_size': fields.Integer(required=True, description = 'The size of the patient subgroup B (to)'),
	'rel_risk': fields.Float(required=True, description = 'The relative risk of comorbidity')
})

simple_disease_group_model = DISEASE_NS.model('SimpleDiseaseGroup', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease group'),
	'name': fields.String(required=True, description = 'The disease group symbolic name')
})

simple_disease_group_model_schema = DISEASE_NS.schema_model('SimpleDiseaseGroup', {
	'description': 'A disease group describedç in the comorbidities database',
	'properties': {
		'id': {
			'type': 'integer',
			'description': 'The internal id of the disease group'
		},
		'name': {
			'type': 'string',
			'description': 'The disease group symbolic name'
		}
	},
	'type': 'object',
	'required': ['id','name']
})

disease_group_model = DISEASE_NS.model('DiseaseGroup', {
	'id': fields.Integer(required=True, description = 'The internal id of the disease group'),
	'name': fields.String(required=True, description = 'The disease group symbolic name'),
	'color': fields.String(required=True, description = 'Preferred color for this group of diseases')
})


PATIENT_NS = Namespace('patients','Patients')

patient_model = PATIENT_NS.model('Patient',{
	'id': fields.Integer(required=True, description = 'The internal id of the patient'),
	'patient_subgroup_id':  fields.Integer(required=True, description = 'The internal id of the patient subgroup where this patient is'),
	'study_id': fields.String(required=True, description = 'The id of the study in the original source')
})

simple_patient_model = patient_model

patient_subgroup_model = PATIENT_NS.model('PatientSubgroup',{
	'id': fields.Integer(required=True, description = 'The internal id of the patient subgroup'),
	'name': fields.String(required=True, description = 'The patient subgroup symbolic name'),
	'disease_id': fields.Integer(required=True, description = 'The internal id of the disease this patient subgroup is related to'),
	'size': fields.Integer(required=True, description = 'The number of patients in this subgroup')
})

simple_patient_subgroup_model = patient_subgroup_model

patients_interaction_model = PATIENT_NS.model('PatientsInteraction', {
	'patient_i_id': fields.Integer(required=True, description = 'The internal id of patient I'),
	'patient_j_id': fields.Integer(required=True, description = 'The internal id of patient J'),
	'interaction_sign': fields.Integer(required=True, description = 'The interaction sign between I and J')
})

intersect_genes_model = PATIENT_NS.model('IntersectGenes',{
	'gene_symbol': fields.String(required=True, description = 'The gene symbol'),
	'regulation_sign': fields.Integer(required=True, description = 'The regulation sign of this gene for this patient or patient subgroup')
})
map_genes_model = intersect_genes_model


intersect_drugs_model = PATIENT_NS.model('IntersectDrugs',{
	'drug_id': fields.Integer(required=True, description = 'The internal drug id'),
	'regulation_sign': fields.Integer(required=True, description = 'The regulation sign of this drug for this patient or patient subgroup')
})
map_drugs_model = intersect_drugs_model

patient_subgroup_intersect_genes_model = PATIENT_NS.model('PatientSubgroupIntersectGenes',{
	'patient_subgroup_id': fields.Integer(required=True, description = 'The internal id of the patient subgroup'),
	'genes': fields.List(fields.Nested(intersect_genes_model), required=True, description = 'The list of genes with common behavior in this patient subgroup')
})


patient_subgroup_intersect_drugs_model = PATIENT_NS.model('PatientSubgroupIntersectDrugs',{
	'patient_subgroup_id': fields.Integer(required=True, description = 'The internal id of the patient subgroup'),
	'drugs': fields.List(fields.Nested(intersect_drugs_model), required=True, description = 'The list of drugs with common behavior in this patient subgroup')
})

patient_map_genes_model = PATIENT_NS.model('PatientMapGenes',{
	'patient_id': fields.Integer(required=True, description = 'The internal id of the patient'),
	'genes': fields.List(fields.Nested(map_genes_model), required=True, description = 'The list of genes with common behavior in this patient')
})


patient_map_drugs_model = PATIENT_NS.model('PatientMapDrugs',{
	'patient_id': fields.Integer(required=True, description = 'The internal id of the patient'),
	'drugs': fields.List(fields.Nested(map_drugs_model), required=True, description = 'The list of drugs with common behavior in this patient')
})
