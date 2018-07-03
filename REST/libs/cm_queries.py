#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

#import sys, os

import sqlite3
import urllib


# This class manages all the database queries
class ComorbiditiesNetwork(object):
	def __init__(self,dbpath,api,itersize=100):
		self.api = api
		self.db = sqlite3.connect('file:'+urllib.parse.quote(dbpath)+'?mode=ro',uri=True, check_same_thread=False)
		self.dbpath = dbpath
		self.itersize = itersize
	
	def _getCursor(self):
		cur = self.db.cursor()
		cur.arraysize = self.itersize
		return cur
		
	def genes(self,symbol=None):
		res = []
		cur = self._getCursor()
		try:
			if symbol is not None:
				cur.execute('SELECT gene_symbol,ensembl_id,uniprot_id FROM gene WHERE gene_symbol = ?',(symbol,))
			else:
				cur.execute('SELECT gene_symbol,ensembl_id,uniprot_id FROM gene')
			while True:
				genes = cur.fetchmany()
				if len(genes)==0:
					if len(res) == 0:
						if symbol is not None:
							self.api.abort(404, "Gene {} is not found in the database".format(symbol))
						else:
							self.api.abort(500,"Empty comorbidities database")
					break
				
				res.extend(map(lambda gene: {
						'symbol': gene[0],
						'ensembl_id': gene[1],
						'uniprot_acc': gene[2]
					},genes))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def gene(self,symbol):
		res = self.genes(symbol=symbol)
		
		return res[0]
	
	def drugs(self,drug_id=None):
		res = []
		cur = self._getCursor()
		try:
			if drug_id is not None:
				cur.execute('SELECT id,name FROM drug WHERE id = ?',(drug_id,))
			else:
				cur.execute('SELECT id,name FROM drug')
			while True:
				drugs = cur.fetchmany()
				if len(drugs)==0:
					if len(res) == 0:
						if drug_id is not None:
							self.api.abort(404, "Drug {} is not found in the database".format(drug_id))
						else:
							self.api.abort(500,"Empty comorbidities database")
					break
				
				res.extend(map(lambda drug: {'id': drug[0],'name': drug[1]},drugs))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def drug(self,id):
		res = self.drugs(drug_id = id)
		
		return res[0]

	@staticmethod
	def _formatStudy(study_id):
		return {'id': study_id,'source': 'GEO'  if study_id.startswith('GSE')  else 'ArrayExpress' }
	
	def studies(self,study_id=None):
		res = []
		cur = self._getCursor()
		try:
			if study_id is not None:
				cur.execute('SELECT geo_arrayexpress_code FROM study WHERE geo_arrayexpress_code = ?',(study_id,))
			else:
				cur.execute('SELECT geo_arrayexpress_code FROM study')
			while True:
				studies = cur.fetchmany()
				if len(studies)==0:
					if len(res)==0:
						if study_id is not None:
							self.api.abort(404, "Study {} is not found in the database".format(study_id))
						else:
							self.api.abort(500,"Empty comorbidities database")
					break
				
				res.extend(map(lambda study: ComorbiditiesNetwork._formatStudy(study[0]) ,studies))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def study(self,study_id):
		res = self.studies(study_id)
		
		return res[0]
	
	def disease_groups(self,disease_group_id=None):
		res = []
		cur = self._getCursor()
		try:
			if disease_group_id is not None:
				cur.execute('SELECT dg.id,dg.name,dgp.property,dgp.value FROM disease_group dg LEFT JOIN disease_group_properties dgp ON dgp.disease_group_id = dg.id WHERE dg.id = ? ORDER BY 1',(disease_group_id,))
			else:
				cur.execute('SELECT dg.id,dg.name,dgp.property,dgp.value FROM disease_group dg LEFT JOIN disease_group_properties dgp ON dgp.disease_group_id = dg.id ORDER BY 1')
			minires = None
			while True:
				dg_props = cur.fetchmany()
				if len(dg_props) == 0:
					# Empty dictionary?
					if len(res) == 0:
						if disease_group_id is not None:
							self.api.abort(404, "Disease group {} is not found in the database".format(disease_group_id))
						else:
							self.api.abort(500,"Empty comorbidities database")
					break
				
				for dgp in dg_props:
					# Initializing common properties
					if minires and minires.get('id') != dgp[0]:
						minires = None
					
					if not minires:
						minires = {
							'id': dgp[0],
							'name': dgp[1]
						}
						# In this way we do not have to setup an end condition
						res.append(minires)
					
					if dgp[2] is not None:
						minires[dgp[2]] = dgp[3]
		
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def disease_group(self,id):
		res = self.disease_groups(disease_group_id=id)
		
		return res[0]
	
	def diseases(self,disease_group_id=None,disease_id=None):
		res = []
		cur = self._getCursor()
		try:
			if disease_group_id is not None:
				cur.execute('SELECT d.id,d.name,d.disease_group_id,dp.property,dp.value FROM disease d LEFT JOIN disease_properties dp ON dp.disease_id = d.id WHERE d.disease_group_id = ? ORDER BY 1',(disease_group_id,))
			elif disease_id is not None:
				cur.execute('SELECT d.id,d.name,d.disease_group_id,dp.property,dp.value FROM disease d LEFT JOIN disease_properties dp ON dp.disease_id = d.id WHERE d.id = ? ORDER BY 1',(disease_id,))
			else:
				cur.execute('SELECT d.id,d.name,d.disease_group_id,dp.property,dp.value FROM disease d LEFT JOIN disease_properties dp ON dp.disease_id = d.id ORDER BY 1')
			minires = None
			while True:
				disease_props = cur.fetchmany()
				if len(disease_props) == 0:
					# Empty dictionary?
					if len(res) == 0:
						if disease_group_id is not None:
							self.api.abort(404, "Disease group {} is not found in the database".format(disease_group_id))
						elif disease_id is not None:
							self.api.abort(404, "Disease {} is not found in the database".format(disease_id))
						else:
							self.api.abort(500,"Empty comorbidities database")
					break
				
				for dp in disease_props:
					# Initializing common properties
					if minires and minires.get('id') != dp[0]:
						minires = None
					
					if not minires:
						minires = {
							'id': dp[0],
							'name': dp[1],
							'disease_group_id': dp[2]
						}
						# In this way we do not have to setup an end condition
						res.append(minires)
					
					if dp[3] is not None:
						minires[dp[3]] = dp[4]
		
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def disease(self,disease_id):
		res = self.diseases(disease_id=disease_id)
		
		return res[0]
	
	def disease_comorbidities(self,id=None):
		res = None
		cur = self._getCursor()
		try:
			if id is not None:
				cur.execute('SELECT disease_a_id,disease_b_id,relative_risk FROM disease_digraph WHERE disease_a_id = :disease_id OR disease_b_id = :disease_id',{'disease_id': id})
			else:
				cur.execute('SELECT disease_a_id,disease_b_id,relative_risk FROM disease_digraph')
			res = []
			while True:
				disease_co = cur.fetchmany()
				if len(disease_co) == 0:
					# Empty dictionary?
					if not res:
						if id is not None:
							self.api.abort(404, "Disease {} has no comorbidities stored in the database".format(id))
						else:
							self.api.abort(500, "Empty comorbidities database")
					break
				
				res.extend(map(lambda co: {'from_id': co[0], 'to_id': co[1], 'rel_risk': co[2] },disease_co))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def diseases_patient_subgroups_comorbidities(self,disease_ids,min_subgroup_size=None):
		disease_ids_set = set(disease_ids)
		if len(disease_ids_set) < 2:
			self.api.abort(400, "You must provide at least two different disease ids")
		
		res = None
		
		cur = self._getCursor()
		try:
			subquery_all = '''
SELECT ps.id AS id, COUNT(p.id) AS ps_size
FROM patient_subgroup ps, patient p
WHERE ps.disease_id IN ({})
AND ps.id = p.patient_subgroup_id
GROUP BY ps.id
			'''
			
			subquery_min = '''
SELECT ps.id AS id, COUNT(p.id) AS ps_size
FROM patient_subgroup ps, patient p
WHERE ps.disease_id IN ({})
AND ps.id = p.patient_subgroup_id
GROUP BY ps.id
HAVING ps_size >= ?
			'''
			
			query_template = '''
SELECT psd.patient_subgroup_a_id,
	CASE
		WHEN psd.patient_subgroup_a_id = dps_i.id THEN
		dps_i.ps_size
		ELSE dps_j.ps_size
	END,
	psd.patient_subgroup_b_id,
	CASE
		WHEN psd.patient_subgroup_b_id = dps_i.id THEN
		dps_i.ps_size
		ELSE dps_j.ps_size
	END,
	psd.relative_risk
FROM
(
{0}
) AS dps_i,
(
{0}
) AS dps_j,
	patient_subgroup_digraph psd
WHERE  dps_i.id <> dps_j.id
AND psd.patient_subgroup_a_id = dps_i.id
AND psd.patient_subgroup_b_id = dps_j.id
			'''
			
			
			subquery_template = subquery_all if min_subgroup_size is None else subquery_min
			subquery = subquery_template.format(','.join(['?']*len(disease_ids_set)))
			query = query_template.format(subquery)
			
			query_param_list_base = list(disease_ids_set)
			if min_subgroup_size is not None:
				query_param_list_base.append(min_subgroup_size)
			
			query_param_list = []
			# Yes, it must be done twice, due limitations in
			# the positional parameters manageable by SQLite Python driver
			query_param_list.extend(query_param_list_base)
			query_param_list.extend(query_param_list_base)
			
			cur.execute(query,tuple(query_param_list))
			res = []
			while True:
				pat_sub_co = cur.fetchmany()
				if len(pat_sub_co) == 0:
					# Empty dictionary?
					if not res:
						self.api.abort(404, "No one of the {} different diseases have patient subgroup comorbidities stored in the database".format(len(disease_ids_set)))
					break
				
				res.extend(map(lambda co: {'from_id': co[0], 'from_size':co[1], 'to_id': co[2], 'to_size': co[3], 'rel_risk': co[4] },pat_sub_co))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	
	def patients(self,patient_id=None,patient_subgroup_id=None):
		res = []
		cur = self._getCursor()
		try:
			if patient_subgroup_id is not None:
				cur.execute('SELECT p.id,p.patient_subgroup_id,s.geo_arrayexpress_code FROM patient p, study s WHERE p.study_id = s.id AND patient_subgroup_id = ?',(patient_subgroup_id,))
			elif patient_id is not None:
				cur.execute('SELECT p.id,p.patient_subgroup_id,s.geo_arrayexpress_code FROM patient p, study s WHERE p.study_id = s.id AND p.id = ?',(patient_id,))
			else:
				cur.execute('SELECT p.id,p.patient_subgroup_id,s.geo_arrayexpress_code FROM patient p, study s WHERE p.study_id = s.id')
			while True:
				patients = cur.fetchmany()
				if len(patients)==0:
					if(len(res)==0):
						if patient_subgroup_id is not None:
							self.api.abort(404, "Patient subgroup {} is not found in the database".format(patient_subgroup_id))
						elif patient_id is not None:
							self.api.abort(404, "Patient {} is not found in the database".format(patient_id))
						else:
							self.api.abort(500,"Empty comorbidities database")
					break
				
				res.extend(map(lambda patient: {'id': patient[0],'patient_subgroup_id': patient[1],'study_id': patient[2]},patients))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def patient(self,patient_id):
		res = self.patients(patient_id=patient_id)
		return res[0]
	
	def patient_subgroups(self,patient_subgroup_id=None):
		res = []
		cur = self._getCursor()
		try:
			if patient_subgroup_id is not None:
				query = '''
SELECT ps.id AS id, ps.name AS name, ps.disease_id AS id, COUNT(p.id) AS size
FROM patient_subgroup ps, patient p
WHERE ps.id = ?
AND ps.id = p.patient_subgroup_id
GROUP BY ps.id,ps.name,ps.disease_id
				'''
				cur.execute(query,(patient_subgroup_id,))
			else:
				query = '''
SELECT ps.id AS id, ps.name AS name, ps.disease_id AS id, COUNT(p.id) AS size
FROM patient_subgroup ps, patient p
WHERE ps.id = p.patient_subgroup_id
GROUP BY ps.id,ps.name,ps.disease_id
				'''
				cur.execute(query)
			while True:
				patient_subgroups = cur.fetchmany()
				if len(patient_subgroups)==0:
					if(len(res)==0):
						if patient_subgroup_id is not None:
							self.api.abort(404, "Patient subgroup {} is not found in the database".format(patient_subgroup_id))
						else:
							self.api.abort(500,"Empty comorbidities database")
					break
				
				res.extend(map(lambda ps: {'id': ps[0],'name': ps[1],'disease_id': ps[2], 'size': ps[3]},patient_subgroups))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def patient_subgroup(self,patient_subgroup_id):
		res = self.patient_subgroups(patient_subgroup_id=patient_subgroup_id)
		return res[0]
	
	def patient_subgroup_intersect_genes(self,patient_subgroup_ids=None,disease_ids=None):
		if patient_subgroup_ids is not None and disease_ids is not None:
			self.api.abort(400, "You must provide either a list of patient subgroups or a list of diseases, not both")
		
		if patient_subgroup_ids is not None:
			if len(patient_subgroup_ids) == 0:
				self.api.abort(400, "You must provide at least a patient subgroup")
			
			query_ids_set = set(patient_subgroup_ids)
			
			query_template = '''
SELECT pig.patient_subgroup_id, g.gene_symbol, pig.regulation_sign
FROM patient_subgroup_gene_intersect pig, gene g
WHERE
	pig.patient_subgroup_id IN ({})
AND
	pig.gene_id = g.id
ORDER BY 1,2
			'''
		elif disease_ids is not None:
			if len(disease_ids) == 0:
				self.api.abort(400, "You must provide at lease a disease")
			
			query_id_set = set(disease_ids)
			
			query_template = '''
SELECT pig.patient_subgroup_id, g.gene_symbol, pig.regulation_sign
FROM patient_subgroup ps, patient_subgroup_gene_intersect pig, gene g
WHERE
	ps.disease_id IN ({})
AND
	ps.id = pig.patient_subgroup_id
AND
	pig.gene_id = g.id
ORDER BY 1,2
			'''
		else:
			self.api.abort(400, "You must provide at least a list of patient subgroups or a list of diseases")
		
		res = None
		
		cur = self._getCursor()
		try:
			query = query_template.format(','.join(['?']*len(query_id_set)))
			
			query_param_list = list(query_id_set)
			
			cur.execute(query,tuple(query_param_list))
			res = []
			grouping_id = None
			grouping_list = None
			while True:
				pat_sub_gen = cur.fetchmany()
				if len(pat_sub_gen) == 0:
					# Empty dictionary?
					if not res:
						if patient_subgroup_ids is not None:
							self.api.abort(404, "No one of the {} different patient subgroups have common behavioring drugs to all their patients stored in the database".format(len(query_param_list)))
						elif disease_ids is not None:
							self.api.abort(404, "No one of the patient subgroups related to the {} different diseases have common behavioring drugs to all their patients stored in the database".format(len(query_param_list)))
					break
				
				for inter in pat_sub_gen:
					if grouping_id != inter[0]:
						grouping_id = inter[0]
						grouping_list = []
						res.append({
							'patient_subgroup_id': grouping_id,
							'genes': grouping_list
						})
					grouping_list.append({'gene_symbol': inter[1],'regulation_sign': inter[2]})
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res

	
	def patient_subgroup_intersect_drugs(self,patient_subgroup_ids=None,disease_ids=None):
		if patient_subgroup_ids is not None and disease_ids is not None:
			self.api.abort(400, "You must provide either a list of patient subgroups or a list of diseases, not both")
		
		if patient_subgroup_ids is not None:
			if len(patient_subgroup_ids) == 0:
				self.api.abort(400, "You must provide at least a patient subgroup")
			
			query_ids_set = set(patient_subgroup_ids)
			
			query_template = '''
SELECT patient_subgroup_id, drug_id, regulation_sign
FROM patient_subgroup_drug_intersect
WHERE
	patient_subgroup_id IN ({})
ORDER BY 1,2
			'''
		elif disease_ids is not None:
			if len(disease_ids) == 0:
				self.api.abort(400, "You must provide at lease a disease")
			
			query_id_set = set(disease_ids)
			
			query_template = '''
SELECT psdi.patient_subgroup_id, psdi.drug_id, psdi.regulation_sign
FROM patient_subgroup ps, patient_subgroup_drug_intersect psdi
WHERE
	ps.disease_id IN ({})
AND
	ps.id = psdi.patient_subgroup_id
ORDER BY 1,2
			'''
		else:
			self.api.abort(400, "You must provide at least a list of patient subgroups or a list of diseases")
		
		res = None
		
		cur = self._getCursor()
		try:
			query = query_template.format(','.join(['?']*len(query_id_set)))
			
			query_param_list = list(query_id_set)
			
			cur.execute(query,tuple(query_param_list))
			res = []
			grouping_id = None
			grouping_list = None
			while True:
				pat_sub_drug = cur.fetchmany()
				if len(pat_sub_drug) == 0:
					# Empty dictionary?
					if not res:
						if patient_subgroup_ids is not None:
							self.api.abort(404, "No one of the {} different patient subgroups have common behavioring drugs to all their patients stored in the database".format(len(query_param_list)))
						elif disease_ids is not None:
							self.api.abort(404, "No one of the patient subgroups related to the {} different diseases have common behavioring drugs to all their patients stored in the database".format(len(query_param_list)))
					break
				
				for inter in pat_sub_drug:
					if grouping_id != inter[0]:
						grouping_id = inter[0]
						grouping_list = []
						res.append({
							'patient_subgroup_id': grouping_id,
							'drugs': grouping_list
						})
					grouping_list.append({'drug_id': inter[1],'regulation_sign': inter[2]})
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res

	
	def patient_map_genes(self,patient_subgroup_ids=None,patient_ids=None):
		if patient_subgroup_ids is not None and patient_ids is not None:
			self.api.abort(400, "You must provide either a list of patient subgroups or a list of patients, not both")
		
		if patient_subgroup_ids is not None:
			if len(patient_subgroup_ids) == 0:
				self.api.abort(400, "You must provide at least a patient subgroup")
			query_ids_set = set(patient_subgroup_ids)
			query_template = '''
SELECT pgm.patient_id, g.gene_symbol, pgm.regulation_sign
FROM patient p, patient_gene_maps pgm, gene g
WHERE
	p.patient_subgroup_id IN ({})
AND
	p.id = pgm.patient_id
AND
	pgm.gene_id = g.id
ORDER BY 1,2
			'''
		elif patient_ids is not None:
			if len(patient_ids) == 0:
				self.api.abort(400, "You must provide at least a patient")
			query_ids_set = set(patient_ids)
			query_template = '''
SELECT pgm.patient_id, g.gene_symbol, pgm.regulation_sign
FROM patient_gene_maps pgm, gene g
WHERE
	pgm.patient_id IN ({})
AND
	pgm.gene_id = g.id
ORDER BY 1,2
			'''
		else:
			self.api.abort(400, "You must provide at least a list of patient subgroups or a list of patients")
		
		res = None
		
		cur = self._getCursor()
		try:
			query = query_template.format(','.join(['?']*len(query_ids_set)))
			
			query_param_list = list(query_ids_set)
			
			cur.execute(query,tuple(query_param_list))
			res = []
			grouping_id = None
			grouping_list = None
			while True:
				pat_gen = cur.fetchmany()
				if len(pat_gen) == 0:
					# Empty dictionary?
					if not res:
						if patient_ids is not None:
							self.api.abort(404, "No one of the {} different patients has common behavioring genes on their analyses".format(len(query_param_list)))
						elif patient_subgroup_ids is not None:
							self.api.abort(404, "No patient from the {} different patient subgroups has common behavioring genes on their analyses".format(len(query_param_list)))
					break
				
				for inter in pat_gen:
					if grouping_id != inter[0]:
						grouping_id = inter[0]
						grouping_list = []
						res.append({
							'patient_id': grouping_id,
							'genes': grouping_list
						})
					grouping_list.append({'gene_symbol': inter[1],'regulation_sign': inter[2]})
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res

	
	def patient_map_drugs(self,patient_subgroup_ids=None,patient_ids=None):
		if patient_subgroup_ids is not None and patient_ids is not None:
			self.api.abort(400, "You must provide either a list of patient subgroups or a list of patients, not both")
		
		if patient_subgroup_ids is not None:
			if len(patient_subgroup_ids) == 0:
				self.api.abort(400, "You must provide at least a patient subgroup")
			query_ids_set = set(patient_subgroup_ids)
			query_template = '''
SELECT pdm.patient_id, pdm.drug_id, pdm.regulation_sign
FROM patient p, patient_drug_maps pdm
WHERE
	p.patient_subgroup_id IN ({})
AND
	p.id = pdm.patient_id
ORDER BY 1,2
			'''
		elif patient_ids is not None:
			if len(patient_ids) == 0:
				self.api.abort(400, "You must provide at least a patient")
			query_ids_set = set(patient_ids)
			query_template = '''
SELECT patient_id, drug_id, regulation_sign
FROM patient_drug_maps
WHERE
	patient_id IN ({})
ORDER BY 1,2
			'''
		else:
			self.api.abort(400, "You must provide at least a list of patient subgroups or a list of patients")
		
		res = None
		
		cur = self._getCursor()
		try:
			query = query_template.format(','.join(['?']*len(query_ids_set)))
			
			query_param_list = list(query_ids_set)
			
			cur.execute(query,tuple(query_param_list))
			res = []
			grouping_id = None
			grouping_list = None
			while True:
				pat_drug = cur.fetchmany()
				if len(pat_drug) == 0:
					# Empty dictionary?
					if not res:
						if patient_ids is not None:
							self.api.abort(404, "No one of the {} different patients has common behavioring drugs on their analyses".format(len(query_param_list)))
						elif patient_subgroup_ids is not None:
							self.api.abort(404, "No patient from the {} different patient subgroups has common behavioring drugs on their analyses".format(len(query_param_list)))
					break
				
				for inter in pat_drug:
					if grouping_id != inter[0]:
						grouping_id = inter[0]
						grouping_list = []
						res.append({
							'patient_id': grouping_id,
							'drugs': grouping_list
						})
					grouping_list.append({'drug_id': inter[1],'regulation_sign': inter[2]})
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res

	
	def patients_interactions(self,patient_subgroup_ids=None,patient_ids=None):
		if patient_subgroup_ids is not None and patient_ids is not None:
			self.api.abort(400, "You must provide either a list of patient subgroups or a list of patients, not both")
		
		if patient_subgroup_ids is not None:
			if len(patient_subgroup_ids) == 0:
				self.api.abort(400, "You must provide at least a patient subgroup")
			query_ids_set = set(patient_subgroup_ids)
			query_template = '''
SELECT pg.patient_a_id, pg.patient_b_id, pg.interaction_sign
FROM patient p_i, patient p_j, patient_graph pg
WHERE
	p_i.patient_subgroup_id IN ({0})
AND
	p_j.patient_subgroup_id IN ({0})
AND
	p_i.id = pg.patient_a_id
AND
	p_j.id = pg.patient_b_id
			'''
		elif patient_ids is not None:
			if len(patient_ids) < 2:
				self.api.abort(400, "You must provide at least two patients")
			query_ids_set = set(patient_ids)
			query_template = '''
SELECT patient_a_id, patient_b_id, interaction_sign
FROM patient_graph
WHERE
	patient_a_id IN ({0})
AND
	patient_b_id IN ({0})
			'''
		else:
			self.api.abort(400, "You must provide at least a list of patient subgroups or a list of patients")
		
		res = None
		
		cur = self._getCursor()
		try:
			placeholders = ','.join(['?']*len(query_ids_set))
			query = query_template.format(placeholders)
			
			in_query_param_list = list(query_ids_set)
			query_param_list = []
			
			# It must be done twice, as it is repeated
			query_param_list.extend(in_query_param_list)
			query_param_list.extend(in_query_param_list)
			
			cur.execute(query,tuple(query_param_list))
			res = []
			while True:
				pat_int = cur.fetchmany()
				if len(pat_int) == 0:
					# Empty dictionary?
					if not res:
						if patient_ids is not None:
							self.api.abort(404, "No interactions among the {} different patients, based on their analyses".format(len(in_query_param_list)))
						elif patient_subgroup_ids is not None:
							self.api.abort(404, "No interactions among the patients from the {} different patient subgroups, based on their analyses".format(len(in_query_param_list)))
					break
				
				res.extend(map(lambda pi: {'patient_i_id': pi[0],'patient_j_id': pi[1],'interaction_sign': pi[2]},pat_int))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
