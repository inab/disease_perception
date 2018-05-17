#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask_restplus import Namespace, Resource

from .api_models import *

disease_ns = Namespace('diseases','Diseases')

class DiseaseList(CMResource):
	'''Shows a list of all the diseases'''
	@disease_ns.doc('list_diseases')
	@disease_ns.marshal_list_with(simple_disease_model)
	def get(self):
		'''List all the diseases present in the comorbidity network'''
		return self.cmn.diseases()

@disease_ns.response(404, 'Disease not found')
@disease_ns.param('id', 'The disease id')
class Disease(CMResource):
	'''Return the detailed information of a disease'''
	@disease_ns.doc('disease')
	@disease_ns.marshal_with(disease_model)
	def get(self,id):
		'''It gets detailed disease information'''
		return self.cmn.disease(id)
