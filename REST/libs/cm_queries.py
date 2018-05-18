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
		
	def genes(self):
		res = []
		cur = self._getCursor()
		try:
			cur.execute('SELECT gene_symbol FROM gene')
			while True:
				genes = cur.fetchmany()
				if len(genes)==0:
					break
				
				res.extend(map(lambda gene: {'symbol': gene[0]},genes))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def gene(self,symbol):
		res = None
		cur = self._getCursor()
		try:
			cur.execute('SELECT gene_symbol,ensembl_id,uniprot_id FROM gene WHERE gene_symbol = ?',(symbol,))
			while True:
				gene = cur.fetchone()
				if gene is not None:
					res = {
						'symbol': gene[0],
						'ensembl_id': gene[1],
						'uniprot_acc': gene[2]
					}
				else:
					self.api.abort(404, "Gene {} is not found in the database".format(symbol))
				break
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def drugs(self):
		res = []
		cur = self._getCursor()
		try:
			cur.execute('SELECT id,name FROM drug')
			while True:
				drugs = cur.fetchmany()
				if len(drugs)==0:
					break
				
				res.extend(map(lambda drug: {'id': drug[0],'name': drug[1]},drugs))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def drug(self,id):
		res = None
		cur = self._getCursor()
		try:
			cur.execute('SELECT id,name FROM drug WHERE id = ?',(id,))
			while True:
				drug = cur.fetchone()
				if drug is not None:
					res = {
						'id': drug[0],
						'name': drug[1]
					}
				else:
					self.api.abort(404, "Drug {} is not found in the database".format(id))
				
				break
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res

	@staticmethod
	def _formatStudy(study_id):
		return {'id': study_id,'source': 'GEO'  if study_id.startswith('GSE')  else 'ArrayExpress' }
	
	def studies(self):
		res = []
		cur = self._getCursor()
		try:
			cur.execute('SELECT geo_arrayexpress_code FROM study')
			while True:
				studies = cur.fetchmany()
				if len(studies)==0:
					break
				
				res.extend(map(lambda study: ComorbiditiesNetwork._formatStudy(study[0]) ,studies))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
		
	def study(self,study_id):
		res = None
		cur = self._getCursor()
		try:
			cur.execute('SELECT geo_arrayexpress_code FROM study WHERE geo_arrayexpress_code = ?',(study_id,))
			while True:
				study = cur.fetchone()
				if study is not None:
					res = ComorbiditiesNetwork._formatStudy(study[0])
				else:
					self.api.abort(404, "Study {} is not found in the database".format(study_id))
				
				break
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def disease_groups(self):
		res = []
		cur = self._getCursor()
		try:
			cur.execute('SELECT id,name FROM disease_group')
			while True:
				disease_groups = cur.fetchmany()
				if len(disease_groups)==0:
					break
				
				res.extend(map(lambda dg: {'id': dg[0],'name': dg[1]},disease_groups))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def disease_group(self,id):
		res = None
		cur = self._getCursor()
		try:
			cur.execute('SELECT dg.id,dg.name,dgp.property,dgp.value FROM disease_group dg,disease_group_properties dgp WHERE dg.id = ? AND dgp.disease_group_id = dg.id ORDER BY 1',(id,))
			res = {}
			while True:
				dg_props = cur.fetchmany()
				if len(dg_props) == 0:
					# Empty dictionary?
					if not res:
						self.api.abort(404, "Disease group {} is not found in the database".format(id))
					break
				
				# Initializing common properties
				if not 'id' in res:
					dgp = dg_props[0]
					res = {
						'id': dgp[0],
						'name': dgp[1]
					}
				
				for dgp in dg_props:
					res[dgp[2]] = dgp[3]
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def diseases(self,disease_group_id=None):
		res = []
		cur = self._getCursor()
		try:
			if disease_group_id is not None:
				cur.execute('SELECT id,name,disease_group_id FROM disease WHERE disease_group_id = ?',(disease_group_id,))
			else:
				cur.execute('SELECT id,name,disease_group_id FROM disease')
			while True:
				diseases = cur.fetchmany()
				if len(diseases)==0:
					if(len(res)==0):
						self.api.abort(404, "Disease group {} is not found in the database".format(disease_group_id))
					break
				
				res.extend(map(lambda disease: {'id': disease[0],'name': disease[1],'disease_group_id': disease[2]},diseases))
		finally:
			# Assuring the cursor is properly closed
			cur.close()
		
		return res
	
	def disease(self,id):
		res = None
		cur = self._getCursor()
		try:
			cur.execute('SELECT d.id,d.name,d.disease_group_id,dp.property,dp.value FROM disease d,disease_properties dp WHERE d.id = ? AND dp.disease_id = d.id ORDER BY 1',(id,))
			res = {}
			while True:
				disease_props = cur.fetchmany()
				if len(disease_props) == 0:
					# Empty dictionary?
					if not res:
						self.api.abort(404, "Disease {} is not found in the database".format(id))
					break
				
				# Initializing common properties
				if not 'id' in res:
					dp = disease_props[0]
					res = {
						'id': dp[0],
						'name': dp[1],
						'disease_group_id': dp[2]
					}
				
				for dp in disease_props:
					res[dp[3]] = dp[4]
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