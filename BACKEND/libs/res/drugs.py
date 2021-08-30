#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResource, DRUGS_NS, drug_model

class DrugList(CMResource):
	'''Shows a list of all the drugs related in comorbidity studies'''
	@DRUGS_NS.doc('list_drugs')
	@DRUGS_NS.marshal_list_with(drug_model)
	def get(self):
		'''List all drugs involved in the different studies'''
		return self.cmn.drugs()

@DRUGS_NS.response(404, 'Drug not found')
@DRUGS_NS.param('id', 'The drug id')
class Drug(CMResource):
	'''Return the detailed information of a drug'''
	@DRUGS_NS.doc('drug')
	@DRUGS_NS.marshal_with(drug_model)
	def get(self,id):
		'''It gets detailed drug information'''
		return self.cmn.drug(id)

ROUTES={
	'ns': DRUGS_NS,
	'path': '/drugs',
	'routes': [
		(DrugList,''),
		(Drug,'/<int:id>')
	]
}
