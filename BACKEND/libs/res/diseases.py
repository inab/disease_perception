#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

from .api_models import CMResPath, CMRoutes, CMResource, \
    DISEASE_NS, disease_model, disease_comorbidity_model, \
    disease_patient_subgroup_comorbidity_model, \
    simple_disease_group_model, disease_group_model, \
    patient_subgroup_intersect_genes_model, \
    patient_subgroup_intersect_drugs_model

from flask import redirect
from .nodes import NodesDetailed, NodeById, NodesByName, \
	EdgesFromNodesByName, EdgesFromNodeById, NodesFromNodeById,NodesFromUpperNodes
from .edges import Edges, EdgesFromUpperNodes


class DiseaseList(CMResource):
	'''Shows a list of all the diseases'''
	@DISEASE_NS.doc('list_diseases')
	def get(self):
		'''List all the diseases present in the comorbidity 
			network'''
		return redirect(self.api.url_for(NodesDetailed, h_id=self.default_h_id, 
			n_type='disease'))


@DISEASE_NS.response(404, 'Disease not found')
@DISEASE_NS.param('id', 'The disease id')
class Disease(CMResource):
	'''Return the detailed information of a disease'''
	@DISEASE_NS.doc('disease')
	def get(self,id:str):
		'''It gets detailed disease information'''
		return redirect(self.api.url_for(NodeById, h_id=self.default_h_id, 
			n_type='disease', _id=id))


class ListDiseaseComorbidities(CMResource):
	'''Return the comorbidities network'''
	@DISEASE_NS.doc('disease_comorbidities_network')
	def get(self):
		'''It lists disease comorbidities network'''
		return redirect(self.api.url_for(Edges, h_id=self.default_h_id, 
			e_type='disease_digraph'))


@DISEASE_NS.response(404, 'Disease not found or with no known comorbidity')
@DISEASE_NS.param('id', 'The disease id')
class DiseaseComorbidities(CMResource):
	'''Return the comorbidities of a disease'''
	@DISEASE_NS.doc('disease_comorbidities')
	def get(self,id):
		'''It lists disease comorbidities information'''
		return redirect(self.api.url_for(EdgesFromNodeById, h_id=self.default_h_id, 
			n_type='disease', e_type='disease_digraph', _id=id))


@DISEASE_NS.response(400, 'The number of different disease ids must be at least two')
@DISEASE_NS.response(404, 'No disease found or with no known patient subgroup comorbidity')
@DISEASE_NS.param('disease_ids', 'The disease ids (at least, two), separated by commas')
@DISEASE_NS.param('min_size', 'The minimum size of the subgroups')
class DiseasePatientSubgroupComorbidities(CMResource):
	'''Return the comorbidities of the patient subgroups of a couple of diseases'''
	@DISEASE_NS.doc('disease_ps_comorbidities')
	def get(self,disease_ids, min_size=0):
		'''It lists disease comorbidities information'''
		return redirect(self.api.url_for(EdgesFromUpperNodes, h_id=self.default_h_id, 
			e_type='patient_subgroup_digraph', _id=disease_ids, 
			edges_connection=["disease_has_patient_subgroups","patient_subgroup_has_patients"],
			min_size=min_size))


@DISEASE_NS.response(404, 'No disease found or with no known patient subgroup comorbidity')
@DISEASE_NS.param('disease_ids', 'The disease ids (at least, two), separated by commas')
class DiseasePatientSubgroupIntersectGenes(CMResource):
	'''Return the genes which intersect with the patient subgroups from the diseases'''
	@DISEASE_NS.doc('disease_ps_genes')
	def get(self,disease_ids):
		'''It gets the intersected genes for each patient subgroup related to the input diseases'''
		return redirect(self.api.url_for(NodesFromUpperNodes, h_id=self.default_h_id, 
			n_type='gene', _id=disease_ids, edges_connection=["disease_has_patient_subgroups", "patient_subgroup_gene_intersects"]))


@DISEASE_NS.response(404, 'No disease found or with no known patient subgroup comorbidity')
@DISEASE_NS.param('disease_ids', 'The disease ids (at least, two), separated by commas')
class DiseasePatientSubgroupIntersectDrugs(CMResource):
	'''Return the drugs which intersect with the patient subgroups from the diseases'''
	@DISEASE_NS.doc('disease_ps_drugs')
	def get(self,disease_ids):
		'''It gets the intersected drugs for each patient subgroup related to the input diseases'''
		return redirect(self.api.url_for(NodesFromUpperNodes, h_id=self.default_h_id, 
			n_type='drug', _id=disease_ids, edges_connection=["disease_has_patient_subgroups", "patient_subgroup_drug_intersects"]))


class DiseaseGroupList(CMResource):
	'''Shows a list of all the disease groups'''
	@DISEASE_NS.doc('list_disease_groups')
	def get(self):
		'''List all the disease groups present in the comorbidity network'''
		return redirect(self.api.url_for(NodesDetailed, h_id=self.default_h_id, 
			n_type='disease_group'))


@DISEASE_NS.response(404, 'Disease group not found')
@DISEASE_NS.param('id', 'The disease group id')
class DiseaseGroup(CMResource):
	'''Return the detailed information of a disease group'''
	@DISEASE_NS.doc('disease_group')
	def get(self,id):
		'''It gets detailed disease group information'''
		return redirect(self.api.url_for(NodeById, h_id=self.default_h_id, 
			n_type='disease_group', _id=id))


@DISEASE_NS.response(404, 'Disease group not found')
@DISEASE_NS.param('id', 'The disease group id')
class DiseaseGroupDiseases(CMResource):
	'''Return the disease list of a disease group'''
	@DISEASE_NS.doc('disease_group_list')
	def get(self,id):
		'''It gets the list of diseases in this group'''
		return redirect(self.api.url_for(NodesFromNodeById, h_id=self.default_h_id, 
			n_type='disease_group', e_type=['disease_group_has_diseases'], _id=id))


ROUTES = CMRoutes(
	ns=DISEASE_NS,
	path='/diseases',
	routes=[
		CMResPath(DiseaseList,''),
		CMResPath(Disease,'/<string:id>'),
		CMResPath(DiseaseComorbidities,'/<list(string,sep=","):id>/comorbidities'),
		CMResPath(ListDiseaseComorbidities,'/comorbidities'),
		CMResPath(DiseasePatientSubgroupComorbidities,'/<list(string,sep=","):disease_ids>/patients/subgroups/comorbidities'),
		CMResPath(DiseasePatientSubgroupComorbidities,'/<list(string,sep=","):disease_ids>/patients/subgroups/comorbidities/min_size/<int:min_size>'),
		CMResPath(DiseasePatientSubgroupIntersectGenes,'/<list(string,sep=","):disease_ids>/patients/subgroups/genes'),
		CMResPath(DiseasePatientSubgroupIntersectDrugs,'/<list(string,sep=","):disease_ids>/patients/subgroups/drugs'),
		CMResPath(DiseaseGroupList,'/groups'),
		CMResPath(DiseaseGroupDiseases,'/groups/<list(string,sep=","):id>'),
		CMResPath(DiseaseGroup,'/groups/<string:id>/info')
	]
)
