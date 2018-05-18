#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResource, PSG_NS

class PatientSubgroupList(CMResource):
	'''Shows a list of all the patient subgroups'''

ROUTES={
	'ns': PSG_NS,
	'path': '/patients/subgroups',
	'routes': [
		(PatientSubgroupList,'')
	]
}