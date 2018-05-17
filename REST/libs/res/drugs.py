#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask_restplus import Namespace, Resource

from .api_models import *

drugs_ns = Namespace('drugs','Comorbidities related drugs')

class DrugList(CMResource):
	'''Shows a list of all the drugs related in comorbidity studies'''
	@drugs_ns.doc('list_drugs')
	@drugs_ns.marshal_list_with(simple_drug_model)
	def get(self):
		'''List all drugs involved in the different studies'''
		return self.cmn.drugs()

@drugs_ns.response(404, 'Drug not found')
@drugs_ns.param('id', 'The drug id')
class Drug(CMResource):
	'''Return the detailed information of a drug'''
	@drugs_ns.doc('drug')
	@drugs_ns.marshal_with(drug_model)
	def get(self,id):
		'''It gets detailed drug information'''
		return self.cmn.drug(id)
