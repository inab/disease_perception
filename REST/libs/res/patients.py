#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResource, PATIENT_NS, patient_model, patient_subgroup_model

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

ROUTES={
	'ns': PATIENT_NS,
	'path': '/patients',
	'routes': [
		(PatientList,''),
		(Patient,'/<int:id>'),
		(PatientSubgroupList,'/subgroups'),
		(PatientSubgroupPatients,'/subgroups/<int:id>'),
		(PatientSubgroup,'/subgroups/<int:id>/info'),
	]
}