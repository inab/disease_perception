#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResource, PATIENT_NS, patient_model, patient_subgroup_model, patient_subgroup_intersect_genes_model, patient_subgroup_intersect_drugs_model, patient_map_genes_model, patient_map_drugs_model, patients_interaction_model

class PatientList(CMResource):
	'''Shows a list of all the patient subgroups'''
	@PATIENT_NS.doc('list_patients')
	@PATIENT_NS.marshal_list_with(patient_model)
	def get(self):
		'''List all the patients present in the comorbidity network'''
		return self.cmn.patients()

@PATIENT_NS.response(404, 'Patient not found')
@PATIENT_NS.param('id', 'The patient id')
class Patient(CMResource):
	'''Return the detailed information of a patient'''
	@PATIENT_NS.doc('patient')
	@PATIENT_NS.marshal_with(patient_model)
	def get(self,id):
		'''It gets detailed patient information'''
		return self.cmn.patient(patient_id=id)

@PATIENT_NS.response(404, 'No patient was found')
@PATIENT_NS.param('ids', 'The patient id(s), separated by commas')
class PatientsMapGenes(CMResource):
	'''Return the list of genes which map with the queried patients'''
	@PATIENT_NS.doc('patient_genes')
	@PATIENT_NS.marshal_list_with(patient_map_genes_model)
	def get(self,ids):
		'''It gets the mapped genes for each queried patient'''
		return self.cmn.patient_map_genes(patient_ids=ids)

@PATIENT_NS.response(400, 'The number of different patient ids must be at least two')
@PATIENT_NS.response(404, 'No patient was found')
@PATIENT_NS.param('ids', 'The patient id(s), separated by commas')
class PatientsMapDrugs(CMResource):
	'''Return the list of drugs which map with the queried patients'''
	@PATIENT_NS.doc('patient_drugs')
	@PATIENT_NS.marshal_list_with(patient_map_drugs_model)
	def get(self,ids):
		'''It gets the mapped drugs for each queried patient'''
		return self.cmn.patient_map_drugs(patient_ids=ids)

@PATIENT_NS.response(404, 'No patient was found')
@PATIENT_NS.param('ids', 'The patient id(s), separated by commas')
class PatientsInteraction(CMResource):
	'''Return the interactions among the queried patients'''
	@PATIENT_NS.doc('patients_interaction')
	@PATIENT_NS.marshal_list_with(patients_interaction_model)
	def get(self,ids):
		'''It gets the interactions among the queried patients'''
		return self.cmn.patients_interactions(patient_ids=ids)

class PatientSubgroupList(CMResource):
	'''Shows a list of all the patient subgroups'''
	@PATIENT_NS.doc('list_patient_subgroups')
	@PATIENT_NS.marshal_list_with(patient_subgroup_model)
	def get(self):
		'''List all the patient subgroups present in the comorbidity network'''
		return self.cmn.patient_subgroups()

@PATIENT_NS.response(404, 'Patient subgroup not found')
@PATIENT_NS.param('id', 'The patient subgroup id')
class PatientSubgroup(CMResource):
	'''Return the detailed information of a patient subgroup'''
	@PATIENT_NS.doc('patient_subgroup')
	@PATIENT_NS.marshal_with(patient_subgroup_model)
	def get(self,id):
		'''It gets detailed patient subgroup information'''
		return self.cmn.patient_subgroup(id)

@PATIENT_NS.response(404, 'Patient subgroup not found')
@PATIENT_NS.param('id', 'The patient subgroup id')
class PatientSubgroupPatients(CMResource):
	'''Return the list of patients in a patient subgroup'''
	@PATIENT_NS.doc('patient_subgroup_list')
	@PATIENT_NS.marshal_list_with(patient_model)
	def get(self,id):
		'''It gets the list of patients in this subgroup'''
		return self.cmn.patients(patient_subgroup_id=id)

@PATIENT_NS.response(404, 'No patient subgroup was found')
@PATIENT_NS.param('ids', 'The patient subgroup id(s), separated by commas')
class PatientSubgroupsIntersectGenes(CMResource):
	'''Return the list of genes which intersect with the queried patient subgroups'''
	@PATIENT_NS.doc('patient_subgroup_genes')
	@PATIENT_NS.marshal_list_with(patient_subgroup_intersect_genes_model)
	def get(self,ids):
		'''It gets the intersected genes for each patient subgroup'''
		return self.cmn.patient_subgroup_intersect_genes(patient_subgroup_ids=ids)

@PATIENT_NS.response(404, 'No patient subgroup was found')
@PATIENT_NS.param('ids', 'The patient subgroup id(s), separated by commas')
class PatientSubgroupsIntersectDrugs(CMResource):
	'''Return the list of drugs which intersect with the queried patient subgroups'''
	@PATIENT_NS.doc('patient_subgroup_drugs')
	@PATIENT_NS.marshal_list_with(patient_subgroup_intersect_drugs_model)
	def get(self,ids):
		'''It gets the intersected drugs for each patient subgroup'''
		return self.cmn.patient_subgroup_intersect_drugs(patient_subgroup_ids=ids)

@PATIENT_NS.response(404, 'No patient subgroup was found')
@PATIENT_NS.param('ids', 'The patient subgroup id(s), separated by commas')
class PatientSubgroupPatientsMapGenes(CMResource):
	'''Return the list of genes which map with the patients from the queried patient subgroups'''
	@PATIENT_NS.doc('patient_genes')
	@PATIENT_NS.marshal_list_with(patient_map_genes_model)
	def get(self,ids):
		'''It gets the mapped genes for each patient of the query patient subgroup'''
		return self.cmn.patient_map_genes(patient_subgroup_ids=ids)

@PATIENT_NS.response(404, 'No patient subgroup was found')
@PATIENT_NS.param('ids', 'The patient subgroup id(s), separated by commas')
class PatientSubgroupPatientsMapDrugs(CMResource):
	'''Return the list of drugs which map with the patients from the queried patient subgroups'''
	@PATIENT_NS.doc('patient_drugs')
	@PATIENT_NS.marshal_list_with(patient_map_drugs_model)
	def get(self,ids):
		'''It gets the mapped drugs for each patient of the query patient subgroup'''
		return self.cmn.patient_map_drugs(patient_subgroup_ids=ids)

@PATIENT_NS.response(404, 'No patient subgroup was found')
@PATIENT_NS.param('ids', 'The patient subgroup id(s), separated by commas')
class PatientSubgroupPatientsInteraction(CMResource):
	'''Return the interactions among the patients from the queried patient subgroups'''
	@PATIENT_NS.doc('patient_interactions')
	@PATIENT_NS.marshal_list_with(patients_interaction_model)
	def get(self,ids):
		'''It gets the interactions among the patients of the query patient subgroup'''
		return self.cmn.patients_interactions(patient_subgroup_ids=ids)

ROUTES={
	'ns': PATIENT_NS,
	'path': '/patients',
	'routes': [
		(PatientList,''),
		(Patient,'/<int:id>'),
		(PatientsMapGenes,'/<list(int,sep=","):ids>/genes'),
		(PatientsMapDrugs,'/<list(int,sep=","):ids>/drugs'),
		(PatientsInteraction,'/<list(int,sep=","):ids>/interaction'),
		(PatientSubgroupList,'/subgroups'),
		(PatientSubgroupPatients,'/subgroups/<int:id>'),
		(PatientSubgroupPatients,'/subgroups/<int:id>/patients'),
		(PatientSubgroupsIntersectGenes,'/subgroups/<list(int,sep=","):ids>/genes'),
		(PatientSubgroupsIntersectDrugs,'/subgroups/<list(int,sep=","):ids>/drugs'),
		(PatientSubgroupPatientsMapGenes,'/subgroups/<list(int,sep=","):ids>/patients/genes'),
		(PatientSubgroupPatientsMapDrugs,'/subgroups/<list(int,sep=","):ids>/patients/drugs'),
		(PatientSubgroupPatientsInteraction,'/subgroups/<list(int,sep=","):ids>/patients/interaction'),
		(PatientSubgroup,'/subgroups/<int:id>/info'),
	]
}