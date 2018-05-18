#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResource, DG_NS, simple_disease_group_model, disease_group_model, simple_disease_model

class DiseaseGroupList(CMResource):
	'''Shows a list of all the disease groups'''
	@DG_NS.doc('list_disease_groups')
	@DG_NS.marshal_list_with(simple_disease_group_model)
	def get(self):
		'''List all the disease groups present in the comorbidity network'''
		return self.cmn.disease_groups()

@DG_NS.response(404, 'Disease group not found')
@DG_NS.param('id', 'The disease group id')
class DiseaseGroup(CMResource):
	'''Return the detailed information of a disease group'''
	@DG_NS.doc('disease_group')
	@DG_NS.marshal_with(disease_group_model)
	def get(self,id):
		'''It gets detailed disease group information'''
		return self.cmn.disease_group(id)

@DG_NS.response(404, 'Disease group not found')
@DG_NS.param('id', 'The disease group id')
class DiseaseGroupDiseases(CMResource):
	'''Return the disease list of a disease group'''
	@DG_NS.doc('disease_group_list')
	@DG_NS.marshal_list_with(simple_disease_model)
	def get(self,id):
		'''It gets the list of diseases in this group'''
		return self.cmn.diseases(id)

ROUTES={
	'ns': DG_NS,
	'path': '/diseases/groups',
	'routes': [
		(DiseaseGroupList,''),
		(DiseaseGroup,'/<int:id>'),
		(DiseaseGroupDiseases,'/<int:id>/list')
	]
}