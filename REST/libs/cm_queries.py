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
					if len(res) == 0 and symbol is not None:
						self.api.abort(404, "Gene {} is not found in the database".format(symbol))
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
					if len(res) == 0 and drug_id is not None:
						self.api.abort(404, "Drug {} is not found in the database".format(drug_id))
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
					if len(res)==0 and study_id is not None:
						self.api.abort(404, "Study {} is not found in the database".format(study_id))
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
	
	def disease_comorbidities(self,id):
		res = None
		cur = self._getCursor()
		try:
			cur.execute('SELECT disease_a_id,disease_b_id,relative_risk FROM disease_digraph WHERE disease_a_id = :disease_id OR disease_b_id = :disease_id',{'disease_id': id})
			res = []
			while True:
				disease_co = cur.fetchmany()
				if len(disease_co) == 0:
					# Empty dictionary?
					if not res:
						self.api.abort(404, "Disease {} has no comorbidities stored in the database".format(id))
					break
				
				res.extend(map(lambda co: {'from_id': co[0], 'to_id': co[1], 'rel_risk': co[2] },disease_co))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def diseases_patient_subgroups_comorbidities(self,disease_id_i,disease_id_j,min_subgroup_size=None):
		res = None
		cur = self._getCursor()
		try:
			query_all = '''
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
	SELECT ps.id AS id, COUNT(p.id) AS ps_size
	FROM patient_subgroup ps, patient p
	WHERE ps.disease_id = :disease_id_i
	AND ps.id = p.patient_subgroup_id
	GROUP BY ps.id
) AS dps_i,
(
	SELECT ps.id AS id, COUNT(p.id) AS ps_size
	FROM patient_subgroup ps, patient p
	WHERE ps.disease_id = :disease_id_j
	AND ps.id = p.patient_subgroup_id
	GROUP BY ps.id
) AS dps_j,
	patient_subgroup_digraph psd
WHERE  ( psd.patient_subgroup_a_id = dps_i.id
	AND psd.patient_subgroup_b_id = dps_j.id )
OR
	( psd.patient_subgroup_a_id = dps_j.id
	AND psd.patient_subgroup_b_id = dps_i.id )
			'''
			query_min = '''
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
	SELECT ps.id AS id, COUNT(p.id) AS ps_size
	FROM patient_subgroup ps, patient p
	WHERE ps.disease_id = :disease_id_i
	AND ps.id = p.patient_subgroup_id
	GROUP BY ps.id
	HAVING ps_size >= :min_size
) AS dps_i,
(
	SELECT ps.id AS id, COUNT(p.id) AS ps_size
	FROM patient_subgroup ps, patient p
	WHERE ps.disease_id = :disease_id_j
	AND ps.id = p.patient_subgroup_id
	GROUP BY ps.id
	HAVING ps_size >= :min_size
) AS dps_j,
	patient_subgroup_digraph psd
WHERE  ( psd.patient_subgroup_a_id = dps_i.id
	AND psd.patient_subgroup_b_id = dps_j.id )
OR
	( psd.patient_subgroup_a_id = dps_j.id
	AND psd.patient_subgroup_b_id = dps_i.id )
			'''
			query = query_all if min_subgroup_size is None else query_min
			cur.execute(query,{
				'disease_id_i': disease_id_i,
				'disease_id_j': disease_id_j,
				'min_size': min_subgroup_size
			})
			res = []
			while True:
				pat_sub_co = cur.fetchmany()
				if len(pat_sub_co) == 0:
					# Empty dictionary?
					if not res:
						self.api.abort(404, "Diseases {} and {} have no patient subgroup comorbidities stored in the database".format(disease_id_i,disease_id_j))
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
				cur.execute('SELECT id,name,disease_id FROM patient_subgroup WHERE id = ?',(patient_subgroup_id,))
			else:
				cur.execute('SELECT id,name,disease_id FROM patient_subgroup')
			while True:
				patient_subgroups = cur.fetchmany()
				if len(patient_subgroups)==0:
					if(len(res)==0):
						if patient_subgroup_id is not None:
							self.api.abort(404, "Patient subgroup {} is not found in the database".format(patient_subgroup_id))
					break
				
				res.extend(map(lambda ps: {'id': ps[0],'name': ps[1],'disease_id': ps[2]},patient_subgroups))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def patient_subgroup(self,patient_subgroup_id):
		res = self.patient_subgroups(patient_subgroup_id=patient_subgroup_id)
		return res[0]
