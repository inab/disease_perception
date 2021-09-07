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