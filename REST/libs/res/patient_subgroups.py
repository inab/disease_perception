#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask_restplus import Namespace, Resource

from .api_models import *

psg_ns = Namespace('patient_subgroups','Patient subgroups')

class PatientSubgroupList(CMResource):
	'''Shows a list of all the patient subgroups'''

