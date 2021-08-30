#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResource, STUDIES_NS, study_model

class StudyList(CMResource):
	'''Shows a list of all the studies used to build the comorbidity network'''
	@STUDIES_NS.doc('list_studies')
	@STUDIES_NS.marshal_list_with(study_model)
	def get(self):
		'''List all the studies used to build the comorbidity network'''
		return self.cmn.studies()

@STUDIES_NS.response(404, 'Study not found')
@STUDIES_NS.param('study_id', 'The study id')
class Study(CMResource):
	'''Return the detailed information of a study'''
	@STUDIES_NS.doc('study')
	@STUDIES_NS.marshal_with(study_model)
	def get(self,study_id):
		'''It gets detailed study information'''
		return self.cmn.study(study_id)

ROUTES={
	'ns': STUDIES_NS,
	'path': '/studies',
	'routes': [
		(StudyList,''),
		(Study,'/<string:study_id>')
	]
}
