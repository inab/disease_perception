#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResPath, CMRoutes, CMResource, \
    STUDIES_NS
from flask import redirect
from .nodes import NodesDetailed, NodesByName, NodeById


class StudyList(CMResource):
	'''Shows a list of all the studies used to build the comorbidity network'''
	@STUDIES_NS.doc('list_studies')
	def get(self):
		'''List all the studies used to build the comorbidity network'''
		return redirect(self.api.url_for(NodesDetailed, h_id=self.default_h_id, n_type='study'))


@STUDIES_NS.response(404, 'Study not found')
@STUDIES_NS.param('study_id', 'The study id')
class Study(CMResource):
	'''Return the detailed information of a study'''
	@STUDIES_NS.doc('study')
	def get(self,study_id):
		'''It gets detailed study information'''
		return redirect(self.api.url_for(NodeById, h_id=self.default_h_id, 
		n_type='study', _id=study_id))


ROUTES = CMRoutes(
	ns=STUDIES_NS,
	path='/studies',
	routes=[
		CMResPath(StudyList,''),
		CMResPath(Study,'/<string:study_id>')
	]
)
