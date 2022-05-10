#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResPath, CMRoutes, CMResource, DRUGS_NS
from flask import redirect
from .nodes import NodesDetailed, NodesByName, NodeById


class DrugList(CMResource):
	'''Shows a list of all the drugs related in comorbidity studies'''
	@DRUGS_NS.doc('list_drugs')
	def get(self):
		'''List all drugs involved in the different studies'''
		return redirect(self.api.url_for(NodesDetailed, h_id=self.default_h_id, 
		n_type='drug'))


@DRUGS_NS.response(404, 'Drug not found')
@DRUGS_NS.param('id', 'The drug id')
class Drug(CMResource):
	'''Return the detailed information of a drug'''
	@DRUGS_NS.doc('drug')
	def get(self,id):
		'''It gets detailed drug information'''
		return redirect(self.api.url_for(NodeById, h_id=self.default_h_id, 
		n_type='drug', _id=id))


ROUTES = CMRoutes(
	ns=DRUGS_NS,
	path='/drugs',
	routes=[
		CMResPath(DrugList,''),
		CMResPath(Drug,'/<string:id>')
	]
)
