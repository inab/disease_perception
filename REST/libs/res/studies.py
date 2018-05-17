#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask_restplus import Namespace, Resource

from .api_models import *

studies_ns = Namespace('studies','Comorbidities related studies')

class StudyList(CMResource):
	'''Shows a list of all the studies used to build the comorbidity network'''
	@studies_ns.doc('list_studies')
	@studies_ns.marshal_list_with(simple_study_model)
	def get(self):
		'''List all the studies used to build the comorbidity network'''
		return self.cmn.studies()

@studies_ns.response(404, 'Study not found')
@studies_ns.param('study_id', 'The study id')
class Study(CMResource):
	'''Return the detailed information of a study'''
	@studies_ns.doc('study')
	@studies_ns.marshal_with(study_model)
	def get(self,study_id):
		'''It gets detailed study information'''
		return self.cmn.study(study_id)
