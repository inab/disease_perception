#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResPath, CMRoutes, CMResource, \
    PATIENT_NS, patient_model, patient_subgroup_model, \
    patient_subgroup_intersect_genes_model, \
    patient_subgroup_intersect_drugs_model, patient_map_genes_model, \
    patient_map_drugs_model, patients_interaction_model

from flask import redirect
from .nodes import NodesDetailed, NodeById, NodesByName, EdgesFromNodesByName, \
	EdgesFromNodeById, NodesFromUpperNodes, NodesFromNodeById

from .edges import EdgesFromUpperNodes


class PatientList(CMResource):
	'''Shows a list of all the patients'''
	@PATIENT_NS.doc('list_patients')
	def get(self):
		'''List all the patients present in the comorbidity network'''
		return redirect(self.api.url_for(NodesDetailed, h_id=self.default_h_id, 
			n_type='patient'))


@PATIENT_NS.response(404, 'Patient not found')
@PATIENT_NS.param('id', 'The patient id')
class Patient(CMResource):
	'''Return the detailed information of a patient'''
	@PATIENT_NS.doc('patient')
	def get(self, id:str):
		'''It gets detailed patient information'''
		return redirect(self.api.url_for(NodeById, h_id=self.default_h_id, 
			n_type='patient', _id=id))


@PATIENT_NS.response(404, 'No patient was found')
@PATIENT_NS.param('ids', 'The patient id(s), separated by commas')
class PatientsMapGenes(CMResource):
	'''Return the list of genes which map with the queried patients'''
	@PATIENT_NS.doc('patient_genes')
	def get(self,ids:str):
		'''It gets the mapped genes for each queried patient'''
		return redirect(self.api.url_for(EdgesFromNodeById, h_id=self.default_h_id, 
			n_type='patient', e_type='patient_gene_maps', _id=ids))


@PATIENT_NS.response(400, 'The number of different patient ids must be at least two')
@PATIENT_NS.response(404, 'No patient was found')
@PATIENT_NS.param('ids', 'The patient id(s), separated by commas')
class PatientsMapDrugs(CMResource):
	'''Return the list of drugs which map with the queried patients'''
	@PATIENT_NS.doc('patient_drugs')
	def get(self,ids):
		'''It gets the mapped drugs for each queried patient'''
		return redirect(self.api.url_for(EdgesFromNodeById, h_id=self.default_h_id, 
			n_type='patient', e_type='patient_drug_maps', _id=ids))


@PATIENT_NS.response(404, 'No patient was found')
@PATIENT_NS.param('ids', 'The patient id(s), separated by commas')
class PatientsInteraction(CMResource):
	'''Return the interactions among the queried patients'''
	@PATIENT_NS.doc('patients_interaction')
	def get(self,ids):
		'''It gets the interactions among the queried patients'''
		return redirect(self.api.url_for(EdgesFromNodeById, h_id=self.default_h_id, 
			n_type='patient', e_type='patient_graph', _id=ids))


class PatientSubgroupList(CMResource):
	'''Shows a list of all the patient subgroups'''
	@PATIENT_NS.doc('list_patient_subgroups')
	def get(self):
		'''List all the patient subgroups present in the comorbidity network'''
		return redirect(self.api.url_for(NodesDetailed, h_id=self.default_h_id, 
			n_type='patient_subgroup'))


@PATIENT_NS.response(404, 'Patient subgroup not found')
@PATIENT_NS.param('id', 'The patient subgroup id')
class PatientSubgroup(CMResource):
	'''Return the detailed information of a patient subgroup'''
	@PATIENT_NS.doc('patient_subgroup')
	def get(self,id):
		'''It gets detailed patient subgroup information'''
		return redirect(self.api.url_for(NodeById, h_id=self.default_h_id, 
			n_type='patient_subgroup', _id=id))


@PATIENT_NS.response(404, 'Patient subgroup not found')
@PATIENT_NS.param('id', 'The patient subgroup id')
class PatientSubgroupPatients(CMResource):
	'''Return the list of patients in a patient subgroup'''
	@PATIENT_NS.doc('patient_subgroup_list')
	def get(self,id):
		'''It gets the list of patients in this subgroup'''
		return redirect(self.api.url_for(NodesFromNodeById, h_id=self.default_h_id, 
			n_type='patient_subgroup', e_type='patient_subgroup_has_patients',
			 _id=id))


@PATIENT_NS.response(404, 'No patient subgroup was found')
@PATIENT_NS.param('ids', 'The patient subgroup id(s), separated by commas')
class PatientSubgroupsIntersectGenes(CMResource):
	'''Return the list of genes which intersect with the queried patient subgroups'''
	@PATIENT_NS.doc('patient_subgroup_genes')
	def get(self,ids):
		'''It gets the intersected genes for each patient subgroup'''
		return redirect(self.api.url_for(NodesFromNodeById, h_id=self.default_h_id, 
			n_type='patient_subgroup', e_type='patient_subgroup_gene_intersects',
			 _id=ids))


@PATIENT_NS.response(404, 'No patient subgroup was found')
@PATIENT_NS.param('ids', 'The patient subgroup id(s), separated by commas')
class PatientSubgroupsIntersectDrugs(CMResource):
	'''Return the list of drugs which intersect with the queried patient subgroups'''
	@PATIENT_NS.doc('patient_subgroup_drugs')
	def get(self,ids):
		'''It gets the intersected drugs for each patient subgroup'''
		return redirect(self.api.url_for(NodesFromNodeById, h_id=self.default_h_id, 
			n_type='patient_subgroup', e_type='patient_subgroup_drug_intersects',
			 _id=ids))


@PATIENT_NS.response(404, 'No patient subgroup was found')
@PATIENT_NS.param('ids', 'The patient subgroup id(s), separated by commas')
class PatientSubgroupPatientsMapGenes(CMResource):
	'''Return the list of genes which map with the patients from the queried patient subgroups'''
	@PATIENT_NS.doc('patient_genes')
	def get(self,ids):
		'''It gets the mapped genes for each patient of the query patient subgroup'''
		#return self.cmn.patient_map_genes(patient_subgroup_ids=ids)
		return redirect(self.api.url_for(NodesFromUpperNodes, h_id=self.default_h_id, 
			n_type='gene', _id=ids, edges_connection=["patient_subgroup_has_patients", "patient_gene_maps"]))


@PATIENT_NS.response(404, 'No patient subgroup was found')
@PATIENT_NS.param('ids', 'The patient subgroup id(s), separated by commas')
class PatientSubgroupPatientsMapDrugs(CMResource):
	'''Return the list of drugs which map with the patients from the queried patient subgroups'''
	@PATIENT_NS.doc('patient_drugs')
	def get(self,ids):
		'''It gets the mapped drugs for each patient of the query patient subgroup'''
		#return self.cmn.patient_map_drugs(patient_subgroup_ids=ids)
		return redirect(self.api.url_for(NodesFromUpperNodes, h_id=self.default_h_id, 
			n_type='drug', _id=ids, edges_connection=["patient_subgroup_has_patients", "patient_drug_maps"]))


@PATIENT_NS.response(404, 'No patient subgroup was found')
@PATIENT_NS.param('ids', 'The patient subgroup id(s), separated by commas')
class PatientSubgroupPatientsInteraction(CMResource):
	'''Return the interactions among the patients from the queried patient subgroups'''
	@PATIENT_NS.doc('patient_interactions')
	def get(self,ids):
		'''It gets the interactions among the patients of the query patient subgroup'''
		#return self.cmn.patients_interactions(patient_subgroup_ids=ids)
		return redirect(self.api.url_for(EdgesFromUpperNodes, h_id=self.default_h_id, 
			e_type='patient_graph', _id=ids, edges_connection=['patient_subgroup_has_patients', ''],min_size=0))


@PATIENT_NS.response(404, 'Patient subgroup not found')
@PATIENT_NS.param('id', 'The patient subgroup id')
class PatientSubgroupPatientsCount(CMResource):
	'''Return the list of patients in a patient subgroup'''
	@PATIENT_NS.doc('patient_subgroup_list_count')
	def get(self,id):
		'''It gets the list of patients in this subgroup'''
		return redirect(self.api.url_for(NodesFromNodeById, h_id=self.default_h_id, 
			n_type='patient_subgroup', e_type='patient_subgroup_has_patients',
			 _id=id))


ROUTES = CMRoutes(
	ns=PATIENT_NS,
	path='/patients',
	routes=[
		CMResPath(PatientList,''),
		CMResPath(Patient,'/<string:id>'),
		CMResPath(PatientsMapGenes,'/<list(string,sep=","):ids>/genes'),
		CMResPath(PatientsMapDrugs,'/<list(string,sep=","):ids>/drugs'),
		CMResPath(PatientsInteraction,'/<list(string,sep=","):ids>/interaction'),
		CMResPath(PatientSubgroupList,'/subgroups'),
		CMResPath(PatientSubgroup,'/subgroups/<string:id>'),
		CMResPath(PatientSubgroupPatients,'/subgroups/<string:id>/patients'),
		CMResPath(PatientSubgroupPatientsCount,'/subgroups/<string:id>/patients/count'),
		CMResPath(PatientSubgroupsIntersectGenes,'/subgroups/<list(string,sep=","):ids>/genes'),
		CMResPath(PatientSubgroupsIntersectDrugs,'/subgroups/<list(string,sep=","):ids>/drugs'),
		CMResPath(PatientSubgroupPatientsMapGenes,'/subgroups/<list(string,sep=","):ids>/patients/genes'),
		CMResPath(PatientSubgroupPatientsMapDrugs,'/subgroups/<list(string,sep=","):ids>/patients/drugs'),
		CMResPath(PatientSubgroupPatientsInteraction,'/subgroups/<list(string,sep=","):ids>/patients/interaction'),
		CMResPath(PatientSubgroup,'/subgroups/<string:id>/info'),
	]
)