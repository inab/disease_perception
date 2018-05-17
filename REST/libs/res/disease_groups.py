#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask_restplus import Namespace, Resource

from .api_models import *

dg_ns = Namespace('disease_groups','Disease groups')

class DiseaseGroupList(CMResource):
	'''Shows a list of all the disease groups'''
	@dg_ns.doc('list_disease_groups')
	@dg_ns.marshal_list_with(simple_disease_group_model)
	def get(self):
		'''List all the disease groups present in the comorbidity network'''
		return self.cmn.disease_groups()

@dg_ns.response(404, 'Disease group not found')
@dg_ns.param('id', 'The disease group id')
class DiseaseGroup(CMResource):
	'''Return the detailed information of a disease group'''
	@dg_ns.doc('disease_group')
	@dg_ns.marshal_with(disease_group_model)
	def get(self,id):
		'''It gets detailed disease group information'''
		return self.cmn.disease_group(id)

@dg_ns.response(404, 'Disease group not found')
@dg_ns.param('id', 'The disease group id')
class DiseaseGroupDiseases(CMResource):
	'''Return the disease list of a disease group'''
	@dg_ns.doc('disease_group_list')
	@dg_ns.marshal_list_with(simple_disease_model)
	def get(self,id):
		'''It gets the list of diseases in this group'''
		return self.cmn.diseases(id)
