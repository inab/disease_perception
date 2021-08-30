#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask_restplus import Namespace, Api, Resource, fields

class CMResource(Resource):
	'''This class eases passing the instance of the comorbidity network query API'''
	def __init__(self,api=None,*args,**kwargs):
		super().__init__(api,*args,**kwargs)
		self.cmn = kwargs['cmnetwork']



NS = Namespace('cm','Comorbidities network info')
#ns = api.namespace('cm', description='Comorbidities network queries')

########################
# The different models #
########################
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