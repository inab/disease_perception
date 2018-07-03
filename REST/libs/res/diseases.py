#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResource, DISEASE_NS, disease_model, disease_comorbidity_model, disease_patient_subgroup_comorbidity_model, simple_disease_group_model, disease_group_model, patient_subgroup_intersect_genes_model, patient_subgroup_intersect_drugs_model

class DiseaseList(CMResource):
	'''Shows a list of all the diseases'''
	@DISEASE_NS.doc('list_diseases')
	@DISEASE_NS.marshal_list_with(disease_model)
	def get(self):
		'''List all the diseases present in the comorbidity network'''
		return self.cmn.diseases()

@DISEASE_NS.response(404, 'Disease not found')
@DISEASE_NS.param('id', 'The disease id')
class Disease(CMResource):
	'''Return the detailed information of a disease'''
	@DISEASE_NS.doc('disease')
	@DISEASE_NS.marshal_with(disease_model)
	def get(self,id):
		'''It gets detailed disease information'''
		return self.cmn.disease(id)

class ListDiseaseComorbidities(CMResource):
	'''Return the comorbidities network'''
	@DISEASE_NS.doc('disease_comorbidities_network')
	@DISEASE_NS.marshal_list_with(disease_comorbidity_model)
	def get(self):
		'''It lists disease comorbidities network'''
		return self.cmn.disease_comorbidities()

@DISEASE_NS.response(404, 'Disease not found or with no known comorbidity')
@DISEASE_NS.param('id', 'The disease id')
class DiseaseComorbidities(CMResource):
	'''Return the comorbidities of a disease'''
	@DISEASE_NS.doc('disease_comorbidities')
	@DISEASE_NS.marshal_list_with(disease_comorbidity_model)
	def get(self,id):
		'''It lists disease comorbidities information'''
		return self.cmn.disease_comorbidities(id)

@DISEASE_NS.response(400, 'The number of different disease ids must be at least two')
@DISEASE_NS.response(404, 'No disease found or with no known patient subgroup comorbidity')
@DISEASE_NS.param('disease_ids', 'The disease ids (at least, two), separated by commas')
@DISEASE_NS.param('min_size', 'The minimum size of the subgroups')
class DiseasePatientSubgroupComorbidities(CMResource):
	'''Return the comorbidities of the patient subgroups of a couple of diseases'''
	@DISEASE_NS.doc('disease_ps_comorbidities')
	@DISEASE_NS.marshal_list_with(disease_patient_subgroup_comorbidity_model)
	def get(self,disease_ids,min_size=None):
		'''It lists disease comorbidities information'''
		return self.cmn.diseases_patient_subgroups_comorbidities(disease_ids,min_size)

@DISEASE_NS.response(404, 'No disease found or with no known patient subgroup comorbidity')
@DISEASE_NS.param('disease_ids', 'The disease ids (at least, two), separated by commas')
class DiseasePatientSubgroupIntersectGenes(CMResource):
	'''Return the genes which intersect with the patient subgroups from the diseases'''
	@DISEASE_NS.doc('disease_ps_genes')
	@DISEASE_NS.marshal_list_with(patient_subgroup_intersect_genes_model)
	def get(self,disease_ids):
		'''It gets the intersected genes for each patient subgroup related to the input diseases'''
		return self.cmn.patient_subgroup_intersect_genes(disease_ids=disease_ids)

@DISEASE_NS.response(404, 'No disease found or with no known patient subgroup comorbidity')
@DISEASE_NS.param('disease_ids', 'The disease ids (at least, two), separated by commas')
class DiseasePatientSubgroupIntersectDrugs(CMResource):
	'''Return the drugs which intersect with the patient subgroups from the diseases'''
	@DISEASE_NS.doc('disease_ps_drugs')
	@DISEASE_NS.marshal_list_with(patient_subgroup_intersect_drugs_model)
	def get(self,disease_ids):
		'''It gets the intersected drugs for each patient subgroup related to the input diseases'''
		return self.cmn.patient_subgroup_intersect_drugs(disease_ids=disease_ids)


class DiseaseGroupList(CMResource):
	'''Shows a list of all the disease groups'''
	@DISEASE_NS.doc('list_disease_groups')
	@DISEASE_NS.marshal_list_with(disease_group_model)
	def get(self):
		'''List all the disease groups present in the comorbidity network'''
		return self.cmn.disease_groups()

@DISEASE_NS.response(404, 'Disease group not found')
@DISEASE_NS.param('id', 'The disease group id')
class DiseaseGroup(CMResource):
	'''Return the detailed information of a disease group'''
	@DISEASE_NS.doc('disease_group')
	@DISEASE_NS.marshal_with(disease_group_model)
	def get(self,id):
		'''It gets detailed disease group information'''
		return self.cmn.disease_group(id)

@DISEASE_NS.response(404, 'Disease group not found')
@DISEASE_NS.param('id', 'The disease group id')
class DiseaseGroupDiseases(CMResource):
	'''Return the disease list of a disease group'''
	@DISEASE_NS.doc('disease_group_list')
	@DISEASE_NS.marshal_list_with(disease_model)
	def get(self,id):
		'''It gets the list of diseases in this group'''
		return self.cmn.diseases(disease_group_id=id)

ROUTES={
	'ns': DISEASE_NS,
	'path': '/diseases',
	'routes': [
		(DiseaseList,''),
		(Disease,'/<int:id>'),
		(DiseaseComorbidities,'/<int:id>/comorbidities'),
		(ListDiseaseComorbidities,'/comorbidities'),
		(DiseasePatientSubgroupComorbidities,'/<list(int,sep=","):disease_ids>/patients/subgroups/comorbidities'),
		(DiseasePatientSubgroupComorbidities,'/<list(int,sep=","):disease_ids>/patients/subgroups/comorbidities/min_size/<int:min_size>'),
		(DiseasePatientSubgroupIntersectGenes,'/<list(int,sep=","):disease_ids>/patients/subgroups/genes'),
		(DiseasePatientSubgroupIntersectDrugs,'/<list(int,sep=","):disease_ids>/patients/subgroups/drugs'),
		(DiseaseGroupList,'/groups'),
		(DiseaseGroupDiseases,'/groups/<int:id>'),
		(DiseaseGroup,'/groups/<int:id>/info')
	]
}
