#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from flask import Flask
from flask_restplus import Namespace, Resource
from flask_cors import CORS

from .cm_queries import ComorbiditiesNetwork

from .res.api_models import init_comorbidities_api

from .res.ns import ns
from .res.genes import genes_ns,GeneList,Gene
from .res.drugs import drugs_ns,DrugList,Drug
from .res.studies import studies_ns,StudyList,Study
from .res.disease_groups import dg_ns,DiseaseGroupList,DiseaseGroup,DiseaseGroupDiseases
from .res.diseases import disease_ns,DiseaseList,Disease
from .res.patient_subgroups import psg_ns,PatientSubgroupList

def _register_cm_namespaces(api,res_kwargs):
	# Registering the different namespaces, along with their paths
	api.add_namespace(ns)
	
	# Genes
	api.add_namespace(genes_ns,path='/genes')
	genes_ns.add_resource(GeneList,'',resource_class_kwargs=res_kwargs)
	genes_ns.add_resource(Gene,'/<symbol>',resource_class_kwargs=res_kwargs)
	
	# Drugs
	api.add_namespace(drugs_ns,path='/drugs')

	drugs_ns.add_resource(DrugList,'',resource_class_kwargs=res_kwargs)
	drugs_ns.add_resource(Drug,'/<int:id>',resource_class_kwargs=res_kwargs)
	
	# Studies
	api.add_namespace(studies_ns,path='/studies')

	studies_ns.add_resource(StudyList,'',resource_class_kwargs=res_kwargs)
	studies_ns.add_resource(Study,'/<study_id>',resource_class_kwargs=res_kwargs)
	
	# Diseases groups
	api.add_namespace(dg_ns,path='/diseases/groups')
	
	dg_ns.add_resource(DiseaseGroupList,'',resource_class_kwargs=res_kwargs)
	dg_ns.add_resource(DiseaseGroup,'/<int:id>',resource_class_kwargs=res_kwargs)
	dg_ns.add_resource(DiseaseGroupDiseases,'/<int:id>/list',resource_class_kwargs=res_kwargs)
	
	# Diseases
	api.add_namespace(disease_ns,path='/diseases')
	
	disease_ns.add_resource(DiseaseList,'',resource_class_kwargs=res_kwargs)
	disease_ns.add_resource(Disease,'/<int:id>',resource_class_kwargs=res_kwargs)
	
	# Patient subgroups
	api.add_namespace(psg_ns,path='/patients/subgroups')
	
	psg_ns.add_resource(PatientSubgroupList,'',resource_class_kwargs=res_kwargs)

def init_comorbidities_app(dbpath):
	app = Flask('como_network')

	# This enables CORS along all the app
	cors = CORS(app)

	# Attaching the API to the app 
	api = init_comorbidities_api(app)
	
	# This is the singleton instance shared by all the resources
	CMNetwork = ComorbiditiesNetwork(dbpath,api)
	
	res_kwargs = {'cmnetwork': CMNetwork}
	
	_register_cm_namespaces(api,res_kwargs)
	
	return app