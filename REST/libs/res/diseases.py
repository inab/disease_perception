#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResource, DISEASE_NS, simple_disease_model, disease_model, simple_disease_group_model, disease_group_model

class DiseaseList(CMResource):
	'''Shows a list of all the diseases'''
	@DISEASE_NS.doc('list_diseases')
	@DISEASE_NS.marshal_list_with(simple_disease_model)
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


class DiseaseGroupList(CMResource):
	'''Shows a list of all the disease groups'''
	@DISEASE_NS.doc('list_disease_groups')
	@DISEASE_NS.marshal_list_with(simple_disease_group_model)
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
	@DISEASE_NS.marshal_list_with(simple_disease_model)
	def get(self,id):
		'''It gets the list of diseases in this group'''
		return self.cmn.diseases(disease_group_id=id)

ROUTES={
	'ns': DISEASE_NS,
	'path': '/diseases',
	'routes': [
		(DiseaseList,''),
		(Disease,'/<int:id>'),
		(DiseaseGroupList,'/groups'),
		(DiseaseGroupDiseases,'/groups/<int:id>'),
		(DiseaseGroup,'/groups/<int:id>/info')
	]
}