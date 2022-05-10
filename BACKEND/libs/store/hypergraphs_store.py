#!/usr/bin/env python3

import sqlite3
try:
	# Trying to load a newer version
	import pysqlite3
	if pysqlite3.sqlite_version_info > sqlite3.sqlite_version_info:
		del sqlite3
		import pysqlite3 as sqlite3
	else:
		del pysqlite3
except:
	pass

import json
import logging
import os
import os.path
from typing import Any, Iterable, Iterator, List, Mapping, Tuple, Optional , Union
import urllib.parse
import sys

import filetype
import jsonschema

# We have preference for the C based loader and dumper, but the code
# should fallback to default implementations when C ones are not present
import yaml
try:
	from yaml import CLoader as YAMLLoader, CDumper as YAMLDumper
except ImportError:
	from yaml import Loader as YAMLLoader, Dumper as YAMLDumper

from .common import *
from .tabular_parsers import *


class HypergraphsStoreException(Exception):
	pass

class HypergraphsStore(object):
	SQL_SCHEMA_FILENAME = 'hypergraphs_schema.sql'
	MANIFEST_SCHEMAS_RELDIR = 'manifests'
	METADATA_MANIFEST_JSONSCHEMA_FILENAME = 'metadata-manifest.json'
	DATA_MANIFEST_JSONSCHEMA_FILENAME = 'data-manifest.json'
	
	@staticmethod
	def _detect_extensions(keywords: List[str] = ['ENABLE_JSON1']) -> bool:
		"""
		Helper method which detects whether used SQLite was
		compiled with all the required extensions
		"""
		conn = sqlite3.connect(':memory:')
		detected = 0
		with conn:
			cur = conn.cursor()
			for res in cur.execute('PRAGMA compile_options;'):
				if res[0] in keywords:
					detected += 1
			cur.close()
		conn.close()
		
		return detected == len(keywords)
	
	def __init__(self, dbfilename:str, readonly:bool = False):
		self.logger = logging.getLogger(self.__class__.__name__)
		# First of all, let's detect JSON1 is available
		if not self._detect_extensions():
			errmsg = "SQLite JSON1 extension is not available. Check your installation"
			self.logger.critical(errmsg)
			raise HypergraphsStoreException(errmsg)
		
		# These are to improve performance
		self.cachedHypergraphs = {}
		self.cachedNodeTypesByName = {}
		self.cachedNodeTypesByInternalId = {}
		self.cachedEdgeTypesByName = {}
		self.cachedEdgeTypesByInternalId = {}
		self.cachedHyperedgeTypesByName = {}
		self.cachedHyperedgeTypesByInternalId = {}
		
		# Connect / create the database
		self._connect_store(dbfilename, readonly=readonly)
		
		self._bootstrap_store()
	
	def getCursor(self, batchSize:Optional[int] = None) -> sqlite3.Cursor:
		"""
		Low level method created to return a cursor to the
		hypergraph database, setting up its batch size
		"""
		cur = self.conn.cursor()
		if isinstance(batchSize, int):
			cur.arraysize = batchSize
		
		return cur
	
	def isStoreBootstrapped(self) -> bool:
		"""
		Helper method to know about the number of tables.
		When there is no table, the store is considered empty.
		"""
		with self.conn:
			cur = self.conn.cursor()
			cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
			numTablesRes = cur.fetchone()
			
			retval = False
			if numTablesRes and numTablesRes[0] > 0:
				self.logger.debug(f"Number of tables: {numTablesRes[0]}")
				retval = True
			cur.close()
			
			return retval
	
	def populateManifest(self, manifest: Union[str, Mapping[str, Any]]) -> Tuple[int, int, int, int]:
		"""
		Manifests are used to declare a bunch of locally stored
		JSON Schemas, used to model the payload of nodes, edges
		and hyperedges, as well as the node types, edge types
		and hyperedge types which use them.
		This method takes as input either a path to a JSON file
		with one of these manifests, or a dictionary following
		the manifest structure, and stores it, along with the
		referred JSON Schemas.
		
		It returns the number of newly stored JSON Schemas, node
		types, edge types and hyperedge types
		"""
		# Initialize store with the manifest
		if not isinstance(manifest, dict):
			with open(manifest, mode="r", encoding="utf-8") as mR:
				manifestObject = json.load(mR)
				manifestBasePath = os.path.dirname(manifest)
		else:
			manifestObject = manifest
			manifestBasePath = None
		
		return self.uploadManifest(manifestObject, manifestBasePath)
		
			
	def _connect_store(self, dbfilename:str, readonly: bool = True) -> sqlite3.Connection:
		"""
		This helper method connects to an SQLite database,
		setting up the connection parameters accordingly to
		whether it should be read-write or read-only
		"""
		self.dbfilename = dbfilename
		if not dbfilename.startswith(':memory:'):
			dburi = 'file:'+urllib.parse.quote(dbfilename)
			isDbUri = True
		else:
			dburi = dbfilename
			isDbUri = False
			
		if readonly:
			dburi += '?mode=ro'
		
		conn = sqlite3.connect(dburi, uri=isDbUri, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES, check_same_thread=False)
		self.conn = conn
		conn.execute("""PRAGMA encoding = 'UTF-8'""")
		conn.execute("""PRAGMA locking_mode = NORMAL""")
		if readonly:
			#conn.execute("""PRAGMA journal_mode = TRUNCATE""")
			conn.execute("""PRAGMA query_only = ON""")
			self.schema_initialized = True
		else:
			conn.execute("""PRAGMA journal_mode = WAL""")
			conn.execute("""PRAGMA foreign_keys = ON""")
			self.schema_initialized = self.isStoreBootstrapped()
		
		return conn
	
	def _bootstrap_store(self) -> None:
		"""
		This helper method bootstraps the store in case it was
		not previously done. Bootstrapping the store means
		declaring the SQL tables and indices needed by it
		"""
		if not self.schema_initialized:
			# First, full path to the schema
			sql_schema_filename = os.path.join(os.path.dirname(__file__), self.SQL_SCHEMA_FILENAME)
			with open(sql_schema_filename, mode="r", encoding="utf-8") as sR:
				sql_script = sR.read()
			
			# Then, store / update the database definition
			with self.conn:
				cur = self.conn.cursor()
				cur.executescript(sql_script)
			
			self.schema_initialized = True
	
	def registeredJSONSchemas(self) -> List[str]:
		"""
		This method returns the list of JSON Schemas already
		stored in the hypergraph store. It is equivalent to
		return the value of the `$id` key from each JSON Schema
		"""
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			for sch in cur.execute('SELECT schema_id FROM json_schemas'):
				retval.append(sch[0])
			cur.close()
		
		return retval
	
	def getJSONSchemaValidator(self, schema_id: str) -> Mapping[str, Any]:
		"""
		This method returns a stored JSON Schema from the
		store, already parsed by `json` library
		"""
		with self.conn:
			cur = self.conn.cursor()
			for pload in cur.execute('SELECT payload FROM json_schemas WHERE schema_id=?',(schema_id,)):
				jsch = json.loads(pload[0])
				jv = jsonschema.validators.validator_for(jsch)(jsch)
				return jv
			cur.close()
		
		return None
	
	def registeredNodeTypes(self) -> List[NodeType]:
		"""
		This method returns the list of declared node types in
		the store, using its corresponding named tuple
		"""
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			for sch in cur.execute('SELECT nt_id, nt_name, node_schema_id FROM node_type'):
				retval.append(NodeType(nt_id=sch[0], name=sch[1], schema_id=sch[2]))
			cur.close()
		
		return retval
	
	def registeredEdgeTypes(self) -> List[EdgeType]:
		"""
		This method returns the list of declared edge types in
		the store, using its corresponding named tuple
		"""
		self._populateNodeTypesCache()
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			for sch in cur.execute('SELECT et_id, et_name, edge_schema_id, weight_name, weight_desc, a_nt_id, b_nt_id FROM edge_type'):
				from_type = self.cachedNodeTypesByInternalId.get(sch[5])
				to_type = self.cachedNodeTypesByInternalId.get(sch[6])
				retval.append(
					EdgeType(
						et_id=sch[0],
						name=sch[1],
						schema_id=sch[2],
						weight_name=sch[3],
						weight_desc=sch[4],
						from_type=from_type,
						to_type=to_type,
					)
				)
			cur.close()
		
		return retval
	
	def registeredHyperedgeTypes(self) -> List[HyperedgeType]:
		"""
		This method returns the list of declared hyperedge types
		in the store, using its corresponding named tuple
		"""
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			for sch in cur.execute('SELECT het_id, het_name, hyperedge_schema_id, weight_name FROM hyperedge_type'):
				retval.append(HyperedgeType(het_id=sch[0], name=sch[1], schema_id=sch[2], weight_name=sch[3]))
			cur.close()
		
		return retval
	
	def expectedNodeTypesForHyperedgeType(self, hetId: InternalHyperedgeTypeId) -> List[NodeType]:
		"""
		Given an internal hyperedge type id, this method returns
		the list of expected node types involved in hyperedges
		of this type
		"""
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			for sch in cur.execute('SELECT het_nt.nt_id, nt.nt_name, nt.node_schema_id FROM hyperedge_type het, hyperedge_type_node_type het_nt, node_type nt WHERE het.het_id = ? AND het.het_id = het_nt.het_id AND het_nt.nt_id = nt.nt_id ORDER BY het_nt.het_nt_id', (hetId,)):
				retval.append(NodeType(nt_id=sch[0], name=sch[1], schema_id=sch[2]))
			cur.close()
		
		return retval
	
	
	def uploadManifest(self, manifest: Mapping[str, Any], manifestBasePath: Optional[str] = None, exist_ok:bool = True) -> Tuple[int, int, int, int]:
		"""
		This method stores all the JSON Schemas, node types,
		edge types and hyperedge types in the hypergraphs store,
		checking their coherence and consistency. As this method
		is reading JSON schemas relative to a path, it takes an
		optional parameter to tell this reference. Also, this
		method's behaviour on duplicates can be controlled.
		"""
		# Validate the manifest
		md_manifest_schema_filename = os.path.join(os.path.dirname(__file__), self.MANIFEST_SCHEMAS_RELDIR, self.METADATA_MANIFEST_JSONSCHEMA_FILENAME)
		with open(md_manifest_schema_filename, mode="r", encoding="utf-8") as mS:
			mdmsF = json.load(mS)

		jv = jsonschema.validators.validator_for(mdmsF)(mdmsF)
		mm_errors = list(jv.iter_errors(instance=manifest))
		if len(mm_errors) > 0:
			errmsg = f'Metadata manifest validation errors: {mm_errors}'
			for iErr, mm_error in enumerate(mm_errors):
				self.logger.error(f'ERROR {iErr} in metadata manifest: {mm_error}')
			raise HypergraphsStoreException(errmsg)
		
		# First, check internal coherence
		schema_ids = set(self.registeredJSONSchemas())
		schemaFiles = []
		if manifestBasePath is None:
			manifestBasePath = os.getcwd()
		
		# The schema files must exist, and be parsable
		for schemaFilename in manifest.get('schemas', []):
			if not os.path.isabs(schemaFilename):
				schemaFilename = os.path.normpath(os.path.join(manifestBasePath, schemaFilename))
			if not os.path.exists(schemaFilename):
				errmsg = f'Schema file {schemaFilename} does not exist'
				self.logger.error(errmsg)
				raise HypergraphsStoreException(errmsg)
			
			with open(schemaFilename, mode="r", encoding="utf-8") as sR:
				schemaFile = sR.read()
			try:
				sF = json.loads(schemaFile)
			except Exception as e:
				errmsg = f'Schema file {schemaFilename} does not contain a valid JSON file'
				self.logger.exception(errmsg)
				raise HypergraphsStoreException(errmsg)
			
			_id = sF.get('$id')
			schema_id = sF.get('$schema')
			if _id is None:
				errmsg = f'Missing $id in JSON file {schemaFilename}. Is it a JSON Schema?'
				self.logger.error(errmsg)
				raise HypergraphsStoreException(errmsg)
			if schema_id is None:
				errmsg = f'Missing $schema in JSON file {schemaFilename}. Is it a JSON Schema?'
				self.logger.error(errmsg)
				raise HypergraphsStoreException(errmsg)
			
			try:
				jv = jsonschema.validators.validator_for(sF)(sF)			
			except Exception as e:
				errmsg = f'Corrupted JSON Schema {schemaFilename}. Reason: {e}'
				self.logger.exception(errmsg)
				raise HypergraphsStoreException(errmsg)
			
			if _id in schema_ids:
				errmsg = f'JSON Schema {_id} from file {schemaFilename} is duplicated'
				if exist_ok:
					self.logger.warning(errmsg + '. Skipping')
					continue
				else:
					self.logger.error(errmsg)
					raise HypergraphsStoreException(errmsg)
			
			# Now, save it for later processing
			schema_ids.add(_id)
			schemaFiles.append(schemaFile)
		
		# Now, let's check the nodes
		node_type_names = set(map(lambda nt: nt.name, self.registeredNodeTypes()))
		loadable_node_types = []
		for node_type in manifest.get('node_types', []):
			nt_name = node_type['name']
			nt_schema_id = node_type['schema_id']
			if nt_schema_id not in schema_ids:
				errmsg = f'Node type {nt_name} depends on missing schema {nt_schema_id}'
				self.logger.error(errmsg)
				raise HypergraphsStoreException(errmsg)
			
			if nt_name in node_type_names:
				errmsg = f'Node type {nt_name} is duplicated'
				if exist_ok:
					self.logger.warning(errmsg + '. Skipping')
					continue
				else:
					self.logger.error(errmsg)
					raise HypergraphsStoreException(errmsg)
			
			node_type_names.add(nt_name)
			loadable_node_types.append(node_type)
		
		# Now, let's check the edges
		edge_type_names = set(map(lambda et: et.name, self.registeredEdgeTypes()))
		loadable_edge_types = []
		for edge_type in manifest.get('edge_types', []):
			et_name = edge_type['name']
			et_schema_id = edge_type['schema_id']
			if et_schema_id not in schema_ids:
				errmsg = f'Edge type {et_name} depends on missing schema {et_schema_id}'
				self.logger.error(errmsg)
				raise HypergraphsStoreException(errmsg)
			
			for nt_key_name in ('node_type_a', 'node_type_b'):
				et_nt_name = edge_type[nt_key_name]
				if et_nt_name not in node_type_names:
					errmsg = f'Edge type {et_name} depends on missing node type {et_nt_name}'
					self.logger.error(errmsg)
					raise HypergraphsStoreException(errmsg)
			
			if et_name in edge_type_names:
				errmsg = f'Edge type {et_name} is duplicated'
				if exist_ok:
					self.logger.warning(errmsg + '. Skipping')
					continue
				else:
					self.logger.error(errmsg)
					raise HypergraphsStoreException(errmsg)
			
			edge_type_names.add(et_name)
			loadable_edge_types.append(edge_type)
		
		# Now, let's check the hyperedges
		hyperedge_type_names = set(map(lambda het: het.name, self.registeredHyperedgeTypes()))
		loadable_hyperedge_types = []
		for het_type in manifest.get('hyperedge_types', []):
			het_name = het_type['name']
			het_schema_id = het_type['schema_id']
			if het_schema_id not in schema_ids:
				errmsg = f'Hyperedge type {het_name} depends on missing schema {het_schema_id}'
				self.logger.error(errmsg)
				raise HypergraphsStoreException(errmsg)
			
			for het_nt_name in het_type['node_types']:
				if het_nt_name not in node_type_names:
					errmsg = f'Hyperedge type {het_name} depends on missing node type {het_nt_name}'
					self.logger.error(errmsg)
					raise HypergraphsStoreException(errmsg)
			
			if het_name in hyperedge_type_names:
				errmsg = f'Hyperedge type {het_name} is duplicated'
				if exist_ok:
					self.logger.warning(errmsg + '. Skipping')
					continue
				else:
					self.logger.error(errmsg)
					raise HypergraphsStoreException(errmsg)
			
			hyperedge_type_names.add(et_name)
			loadable_hyperedge_types.append(het_type)
		
		# Last, it is time to upload
		self._store_schemas(schemaFiles)
		if len(loadable_node_types) > 0:
			self._store_node_types(loadable_node_types)
		if len(loadable_edge_types) > 0:
			self._store_edge_types(loadable_edge_types)
		if len(loadable_hyperedge_types) > 0:
			self._store_hyperedge_types(loadable_hyperedge_types)
		
		return (len(schemaFiles), len(loadable_node_types), len(loadable_edge_types), len(loadable_hyperedge_types))
		
	def _store_schemas(self, schemaFiles: List[str]) -> int:
		"""
		This helper method parses a bunch of read JSON Schema
		files and it stores them in the database
		"""
		with self.conn:
			cur = self.conn.cursor()
			rollback = False
			numLoaded = 0
			try:
				for schemaFile in schemaFiles:
					sch = json.loads(schemaFile)
					cur.execute('INSERT INTO json_schemas(schema_id,payload) VALUES (?, JSON(?))', (sch['$id'], schemaFile))
					numLoaded += 1
			except Exception as e:
				rollback = True
				errmsg = 'Error while loading new schemas'
				self.logger.exception(errmsg)
				raise HypergraphsStoreException(errmsg)
			finally:
				if rollback:
					self.conn.rollback()
				else:
					self.conn.commit()
				cur.close()
		
		self.logger.debug(f"New loaded schemas: {numLoaded}")
		
		return numLoaded
	
	def _store_node_types(self, loadable_node_types: List[Mapping[str, Any]]) -> int:
		"""
		This helper method reads a bunch of node type
		declarations and stores them in the hypergraphs database.
		"""
		numLoaded = 0
		self._invalidateNodeTypesCache()
		with self.conn:
			cur = self.conn.cursor()
			rollback = False
			try:
				cur.executemany('INSERT INTO node_type(nt_name, nt_desc, node_schema_id) VALUES (?, ?, ?)', (
					(nt['name'], nt['desc'], nt['schema_id'])
					for nt in loadable_node_types
				))
				numLoaded = len(loadable_node_types)
			except Exception as e:
				rollback = True
				errmsg = 'Error while loading new node types'
				self.logger.exception(errmsg)
				raise HypergraphsStoreException(errmsg)
			finally:
				if rollback:
					self.conn.rollback()
				else:
					self.conn.commit()
				cur.close()
		
		self.logger.debug(f"New loaded node types: {numLoaded}")
		
		return numLoaded
	
	def _store_edge_types(self, loadable_edge_types: List[Mapping[str, Any]]) -> int:
		"""
		This helper method reads a bunch of edge type
		declarations and stores them in the hypergraphs database.
		"""
		numLoaded = 0
		self._invalidateEdgeTypesCache()
		ntHash = { nt.name: nt.nt_id for nt in self.registeredNodeTypes() }
		with self.conn:
			cur = self.conn.cursor()
			rollback = False
			try:
				cur.executemany('INSERT INTO edge_type(et_name,et_desc,a_nt_id,b_nt_id,is_directed,is_symmetric,edge_schema_id,weight_name,weight_desc) VALUES (?,?,?,?,?,?,?,?,?)', (
					(et['name'], et['desc'], ntHash[et['node_type_a']], ntHash[et['node_type_b']], et['is_directed'], et['is_symmetric'], et['schema_id'], et.get('weight',{}).get('name'), et.get('weight',{}).get('desc'))
					for et in loadable_edge_types
				))
				numLoaded = len(loadable_edge_types)
			except Exception as e:
				rollback = True
				errmsg = 'Error while loading new edge types'
				self.logger.exception(errmsg)
				raise HypergraphsStoreException(errmsg)
			finally:
				if rollback:
					self.conn.rollback()
				else:
					self.conn.commit()
				cur.close()
		
		self.logger.debug(f"New loaded edge types: {numLoaded}")
		
		return numLoaded
	
	def _store_hyperedge_types(self, loadable_hyperedge_types: List[Mapping[str, Any]]) -> int:
		"""
		This helper method reads a bunch of hyperedge type
		declarations and stores them in the hypergraphs database.
		"""
		numLoaded = 0
		self._invalidateHyperedgeTypesCache()
		ntHash = { nt.name: nt.nt_id for nt in self.registeredNodeTypes() }
		with self.conn:
			cur = self.conn.cursor()
			rollback = False
			try:
				# Main body
				cur.executemany('INSERT INTO hyperedge_type(het_name,het_desc,is_tuple,is_directed,is_symmetric,hyperedge_schema_id,weight_name,weight_desc) VALUES (?,?,?,?,?,?,?,?)', (
					(het['name'], het['desc'], het['is_tuple'], het['is_directed'], het['is_symmetric'], het['schema_id'], het.get('weight',{}).get('name'), het.get('weight',{}).get('desc'))
					for het in loadable_hyperedge_types
				))
				
				# Now, get back the new ids
				hetHash = { het.name: het.het_id for het in self.registeredHyperedgeTypes() }
				
				# And, register the expected types of the nodes
				cur.executemany('INSERT INTO hyperedge_type_node_type(het_id,nt_id) VALUES (?,?)', (
					(hetHash[het['name']], ntHash[nt_name])
					for het in loadable_hyperedge_types
					for nt_name in het['node_types']
				))
				
				numLoaded = len(loadable_hyperedge_types)
			except Exception as e:
				rollback = True
				errmsg = 'Error while loading new hyperedge types'
				self.logger.exception(errmsg)
				raise HypergraphsStoreException(errmsg)
			finally:
				if rollback:
					self.conn.rollback()
				else:
					self.conn.commit()
				cur.close()
		
		self.logger.debug(f"New loaded hyperedge types: {numLoaded}")
		
		return numLoaded
	
	def populateDataManifest(self, data_manifest: Union[str, Mapping[str, Any]]) -> None:
		"""
		A data manifest is a declaration of one or more
		hypergraphs to be stored in the hypergraphs store.
		This declaration can be either in a YAML file or already
		read in memory as a dictionary, following the correct
		structure.
		This method takes as input this data manifest, and does
		all the needed work to store or update all the declared
		hypegraphs in the database.
		"""
		# Initialize store with the manifest
		if not isinstance(data_manifest, dict):
			with open(data_manifest, mode="r", encoding="utf-8") as mR:
				data_manifestObject = yaml.load(mR, Loader=YAMLLoader)
				data_manifestBasePath = os.path.dirname(data_manifest)
		else:
			data_manifestObject = data_manifest
			data_manifestBasePath = None
		
		self.uploadDataManifest(data_manifestObject, data_manifestBasePath)
	
	def uploadDataManifest(self, data_manifest: Mapping[str, Any], data_manifestBasePath: Optional[str] = None) -> None:
		"""
		This method validates and uploads/updates the
		hypergraphs declared in the input data manifest. As the
		data manifest points to both hypergraph metadata file
		and all the data files needed to populate the store with
		the hypergraph data, there is an optional parameter to
		tell the reference for relative paths to those files.
		"""
		# Validate the data manifest
		d_manifest_schema_filename = os.path.join(os.path.dirname(__file__), self.MANIFEST_SCHEMAS_RELDIR, self.DATA_MANIFEST_JSONSCHEMA_FILENAME)
		with open(d_manifest_schema_filename, mode="r", encoding="utf-8") as dS:
			dmsF = json.load(dS)
		
		jv = jsonschema.validators.validator_for(dmsF)(dmsF)
		dm_errors = list(jv.iter_errors(instance=data_manifest))
		if len(dm_errors) > 0:
			errmsg = f'Data manifest validation errors: {dm_errors}'
			for iErr, dm_error in enumerate(dm_errors):
				self.logger.error(f'ERROR {iErr} in data manifest: {dm_error}')
			raise HypergraphsStoreException(errmsg)
		
		# Now, let's process each hypergraph to be loaded
		for hypergraphDesc in data_manifest['hypergraphs']:
			self.uploadHypergraph(hypergraphDesc, data_manifestBasePath)
	
	def getHypergraphMetadataId(self, hmId: HypergraphPayloadId) -> HypergraphId:
		"""
		This method takes as input a hypergraph id, as it was
		declared in the hypergraph metadata file when it was
		stored, and it returns a named tuple representing the
		minimal metadata of the hypergraph, including creation
		and update dates.
		"""
		h_id = None
		stored_at = None
		updated_at = None
		with self.conn:
			cur = self.conn.cursor()
			for hm in cur.execute('SELECT h_id, stored_at, updated_at FROM hypergraph WHERE h_payload_id=?', (hmId,)):
				h_id = hm[0]
				stored_at = hm[1]
				updated_at = hm[2]
				break
			cur.close()
		
		return HypergraphId(h_id=h_id, h_payload_id=hmId, stored_at=stored_at, updated_at=updated_at)
	
	def getHypergraphById(self, h_payload_id: HypergraphPayloadId) -> Tuple[HypergraphId, Any]:
		"""
		This method takes as input a hypergraph id, as it was
		declared in the hypergraph metadata file when it was
		stored, and it returns the payload associated to it.
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None, None
		
		payload = None
		with self.conn:
			cur = self.conn.cursor()
			for hm in cur.execute('SELECT payload FROM hypergraph WHERE h_id=?', (hId.h_id,)):
				payload = json.loads(hm[0])
				break
		
		return hId, payload
	
	def _populateHypergraphsCache(self, invalidateCache:bool = False) -> None:
		"""
		This helper method populates an internal cache of the
		correspondence of the public hypergraph ids and their
		minimal metadata.
		"""
		# Only try populating when empty
		if not invalidateCache:
			invalidateCache = len(self.cachedHypergraphs) == 0
		if invalidateCache:
			cur = self.getCursor()
			try:
				self.cachedHypergraphs = {
					hId.h_payload_id: hId
					for hId in self.registeredHypergraphs(cur)
				}
			finally:
				# Assuring the cursor is properly closed
				cur.close()
	
	def _invalidateHypergraphsCache(self) -> None:
		"""
		This helper method invalidates the cached
		correspondences of hypergraph ids and their
		minimal metadata
		"""
		self.cachedHypergraphs = {}
	
	@property
	def hypergraphs(self) ->  Iterator[HypergraphId]:
		"""
		This property returns an iterator to all the known
		hypergraphs minimal metadata
		"""
		self._populateHypergraphsCache()
		return self.cachedHypergraphs.values()
	
	def _populateNodeTypesCache(self, invalidateCache:bool = False) -> None:
		"""
		This helper method populates an internal cache of the
		correspondence of the public node type names and
		internal node type ids with their minimal
		associated metadata.
		"""
		# Only try populating when empty
		if not invalidateCache:
			invalidateCache = len(self.cachedNodeTypesByInternalId) == 0
		if invalidateCache:
			self.cachedNodeTypesByName = {
				ntId.name: ntId
				for ntId in self.registeredNodeTypes()
			}
			self.cachedNodeTypesByInternalId = {
				ntId.nt_id: ntId
				for ntId in self.registeredNodeTypes()
			}
	
	def _invalidateNodeTypesCache(self) -> None:
		"""
		This helper method invalidates the cached
		correspondences of node type names and internal node
		type ids
		"""
		self.cachedNodeTypesByName = {}
		self.cachedNodeTypesByInternalId = {}
	
	@property
	def nodeTypes(self) ->  Iterator[NodeType]:
		"""
		This property returns an iterator to all the known node
		types, whether they are being used in hypergraphs or not.
		"""
		self._populateNodeTypesCache()
		return self.cachedNodeTypesByInternalId.values()
	
	def getNodeTypesByGraph(self, h_payload_id: HypergraphPayloadId, name: Optional[str] = None) -> Iterator[NodeType]:
		"""
		Given a public hypergraph id, it retrieves an iterator
		of nodes types used by nodes in this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT nt.nt_id, nt.nt_name, nt.node_schema_id, nt.nt_desc, nt.payload, (SELECT COUNT(*) FROM node n WHERE n.h_id=? AND n.nt_id=nt.nt_id) AS count
FROM node_type nt
'''
			params = [ hId.h_id ]
			if (name is not None) and len(name) > 0:
				query += ' AND nt.nt_name=?'
				params.append(name)
			for nt in cur.execute(query + ' GROUP BY 1 HAVING count > 0', params):
				retval.append(NodeType(nt_id=nt[0], name=nt[1], schema_id=nt[2], description=nt[3], payload=None if nt[4] is None else json.loads(nt[4]), number=nt[5]))
			cur.close()
		
		return retval
	
	
	def _populateEdgeTypesCache(self, invalidateCache:bool = False) -> None:
		"""
		This helper method populates an internal cache of the
		correspondence of the public edge type names and
		internal edge type ids with their minimal
		associated metadata.
		"""
		# Only try populating when empty
		if not invalidateCache:
			invalidateCache = len(self.cachedEdgeTypesByName) == 0
		if invalidateCache:
			self.cachedEdgeTypesByName = {
				etId.name: etId
				for etId in self.registeredEdgeTypes()
			}
			self.cachedEdgeTypesByInternalId = {
				etId.et_id: etId
				for etId in self.registeredEdgeTypes()
			}
	
	def _invalidateEdgeTypesCache(self) -> None:
		"""
		This helper method invalidates the cached
		correspondences of edge type names and internal edge
		type ids
		"""
		self.cachedEdgeTypesByName = {}
		self.cachedEdgeTypesByInternalId = {}
	
	@property
	def edgeTypes(self) ->  Iterator[EdgeType]:
		"""
		This property returns an iterator to all the known edge
		types, whether they are being used in hypergraphs or not.
		"""
		self._populateEdgeTypesCache()
		return self.cachedEdgeTypesByInternalId.values()
	
	def getMinimalEdgeTypesByGraph(self, h_payload_id: HypergraphPayloadId) -> Iterator[EdgeType]:
		"""
		Given a public hypergraph id, it retrieves an iterator
		of edge types used by edges in this hypergraph. The
		named tuples are filled in with minimal metadata
		information.
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT et.et_id, et.et_name, et.edge_schema_id, (SELECT TRUE FROM edge e WHERE e.h_id=? AND e.et_id=et.et_id LIMIT 1)
FROM edge_type et
'''
			params = [ hId.h_id ]
			for et in cur.execute(query, params):
				retval.append(EdgeType(
					et_id=et[0],
					name=et[1],
					schema_id=et[2],
				))
			cur.close()
		
		return retval
	
	def getEdgeTypesByGraph(self, h_payload_id: HypergraphPayloadId, name: Optional[str] = None) -> Iterator[EdgeType]:
		"""
		Given a public hypergraph id, it retrieves an iterator
		of edge types used by edges in this hypergraph. The
		named tuples are filled in with all the available
		metadata information, including the number of edges.
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateNodeTypesCache()
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT et.et_id, et.et_name, et.edge_schema_id, et.et_desc, et.weight_name, et.weight_desc, et.a_nt_id, et.b_nt_id, et.payload, (SELECT COUNT(*) FROM edge e WHERE e.h_id=? AND e.et_id=et.et_id) AS count
FROM edge_type et
'''
			params = [ hId.h_id ]
			if (name is not None) and len(name) > 0:
				query += ' AND et.et_name=?'
				params.append(name)
			for et in cur.execute(query + 'GROUP BY 1 HAVING count > 0', params):
				from_type = self.cachedNodeTypesByInternalId.get(et[6])
				to_type = self.cachedNodeTypesByInternalId.get(et[7])
				retval.append(EdgeType(
					et_id=et[0],
					name=et[1],
					schema_id=et[2],
					description=et[3],
					weight_name=et[4],
					weight_desc=et[5],
					from_type=from_type,
					to_type=to_type,
					payload=None if et[8] is None else json.loads(et[8]),
					number=et[9]
				))
			cur.close()
		
		return retval
	
	def _populateHyperedgeTypesCache(self, invalidateCache:bool = False) -> None:
		"""
		This helper method populates an internal cache of the
		correspondence of the public hyperedge type names and
		internal hyperedge type ids with their minimal
		associated metadata.
		"""
		if not invalidateCache:
			invalidateCache = len(self.cachedHyperedgeTypesByInternalId) == 0
		if invalidateCache:
			self.cachedHyperedgeTypesByName = {
				hetId.name: hetId
				for hetId in self.registeredHyperedgeTypes()
			}
			self.cachedHyperedgeTypesByInternalId = {
				hetId.het_id: hetId
				for hetId in self.registeredHyperedgeTypes()
			}
	
	def _invalidateHyperedgeTypesCache(self) -> None:
		"""
		This helper method invalidates the cached
		correspondences of hyperedge type names and
		internal hyperedge type ids
		"""
		self.cachedHyperedgeTypesByInternalId = {}
		self.cachedHyperedgeTypesByName = {}
	
	@property
	def hyperedgeTypes(self) ->  Iterator[HyperedgeType]:
		"""
		This property returns an iterator to all the known
		hyperedge types, whether they are being used in
		hypergraphs or not.
		"""
		self._populateHyperedgeTypesCache()
		return self.cachedHyperedgeTypesByInternalId.values()
	
	def getMinimalHyperedgeTypesByGraph(self, h_payload_id: HypergraphPayloadId) -> Iterator[EdgeType]:
		"""
		Given a public hypergraph id, it retrieves an iterator
		of hyperedge types used by hyperedges in this
		hypergraph. The	named tuples are filled in with minimal
		metadata information.
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT het.het_id, het.het_name, het.hyperedge_schema_id, (SELECT TRUE FROM hyperedge he WHERE he.h_id=? AND he.het_id=het.het_id LIMIT 1)
FROM hyperedge_type het
'''
			params = [ hId.h_id ]
			for het in cur.execute(query, params):
				retval.append(HyperedgeType(
					het_id=het[0],
					name=het[1],
					schema_id=het[2],
				))
			cur.close()
		
		return retval
	
	def getHyperedgeTypesByGraph(self, h_payload_id: HypergraphPayloadId, 
		name: Optional[str] = None) -> Iterator[EdgeType]:
		"""
		Given a public hypergraph id, it retrieves an iterator
		of hyperedge types used by hyperedges in this
		hypergraph. The	named tuples are filled in with all the
		available metadata information, including the number of
		hyperedges.
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateNodeTypesCache()
		retval = []
		retvalHash = {}
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT het.het_id, het.het_name, het.hyperedge_schema_id, het.het_desc, het.weight_name, het.weight_desc, het_nt.nt_id, het.payload, (SELECT COUNT(*) FROM hyperedge he WHERE he.h_id=? AND he.het_id=het.het_id) AS count
FROM hyperedge_type het, hyperedge_type_node_type het_nt
WHERE het.het_id = het_nt.het_id
ORDER BY het_nt.het_nt_id
'''
			params = [ hId.h_id ]
			if (name is not None) and len(name) > 0:
				query += ' AND het.het_name=?'
				params.append(name)
			for het in cur.execute(query, params):
				if het[8] == 0:
					continue
				node_type = self.cachedNodeTypesByInternalId.get(het[6])
				hetId = retvalHash.get(het[0])
				if hetId is None:
					hetId = HyperedgeType(
						het_id=het[0],
						name=het[1],
						schema_id=het[2],
						description=het[3],
						weight_name=het[4],
						weight_desc=het[5],
						node_types=[ node_type ],
						payload=None if het[7] is None else json.loads(het[7]),
						number=het[8]
					)
					retval.append(hetId)
					retvalHash[het[0]] = hetId
				else:
					hetId.node_types.append(node_type)
			cur.close()
		
		return retval
	
	def registeredNodes(self, cur: sqlite3.Cursor, h_id: InternalHypergraphId, 
		nt_id: Optional[InternalNodeTypeId] = None) -> List[NodeId]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		retval = []
		query = 'SELECT n_id, nt_id, n_payload_id, n_payload_name FROM node WHERE h_id=?'
		if nt_id is None:
			params = (h_id,)
		else:
			query += ' AND nt_id=?'
			params = (h_id, nt_id)
		for n in cur.execute(query, params):
			retval.append(NodeId(n_id=n[0], nt_id=n[1], n_payload_id=n[2], n_payload_name=n[3]))
		
		return retval
	
	def registeredNodesByGraphAndNodeType(self, h_payload_id: HypergraphPayloadId, 
		nodeTypeName: NodeTypeName) -> List[NodeId]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateNodeTypesCache()
		ntId = self.cachedNodeTypesByName.get(nodeTypeName)
		if ntId is None:
			return None
		
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			query = 'SELECT n_id, nt_id, n_payload_id, n_payload_name FROM node WHERE h_id=? AND nt_id=?'
			params = [hId.h_id, ntId.nt_id]
			for n in cur.execute(query, params):
				retval.append(NodeId(n_id=n[0], nt_id=n[1], n_payload_id=n[2], n_payload_name=n[3]))
			cur.close()
		
		return retval
	
	def getNodesByGraphAndNodeType(self, h_payload_id: HypergraphPayloadId, 
		nodeTypeName: NodeTypeName, names: Optional[List[NodePayloadName]] = None, 
		_ids: Optional[List[NodePayloadId]] = None, internal_ids: Optional[List[InternalNodeId]] = None) -> List[NodeId]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateNodeTypesCache()
		ntId = self.cachedNodeTypesByName.get(nodeTypeName)
		if ntId is None:
			return None
		
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			query = 'SELECT n_id, nt_id, n_payload_id, n_payload_name, payload FROM node WHERE h_id=? AND nt_id=?'
			params = [hId.h_id, ntId.nt_id]
			if (internal_ids is not None) and len(internal_ids) > 0:
				if len(internal_ids) == 1:
					query += ' AND n_id=?'
				else:
					query += f' AND n_id IN ({",".join(["?"] * len(internal_ids))})'
				params.extend(internal_ids)
				
			if (names is not None) and len(names) > 0:
				if len(names) == 1:
					query += ' AND n_payload_name=?'
				else:
					query += f' AND n_payload_name IN ({",".join(["?"] * len(names))})'
				params.extend(names)
				
			if (_ids is not None) and len(_ids) > 0:
				if len(_ids) == 1:
					query += ' AND n_payload_id=?'
				else:
					query += f' AND n_payload_id IN ({",".join(["?"] * len(_ids))})'
				params.extend(_ids)
			
			for n in cur.execute(query, params):
				retval.append(NodeId(n_id=n[0], nt_id=n[1], n_payload_id=n[2], n_payload_name=n[3], payload=None if n[4] is None else json.loads(n[4])))
			cur.close()
		
		return retval
	
	def getEdgesByGraphAndNode(self, h_payload_id: HypergraphPayloadId, nodeTypeName: NodeTypeName, from_to: bool, edgeTypeName: Optional[EdgeTypeName] = None, names: Optional[List[NodePayloadName]] = None, _ids: Optional[List[NodePayloadId]] = None, internal_ids: Optional[List[InternalNodeId]] = None) -> Iterable[Tuple[List[EdgeId], EdgeTypeName]]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateNodeTypesCache()
		ntId = self.cachedNodeTypesByName.get(nodeTypeName)
		if ntId is None:
			return None
		
		self._populateEdgeTypesCache()
		etId = None
		if edgeTypeName is not None:
			etId = self.cachedEdgeTypesByName.get(edgeTypeName)
			if etId is None:
				return None
		
		retval_batches = {}
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT e.e_id, e.et_id, e.e_payload_id, e.e_payload_weight, e.from_id, e.to_id, e.e_payload_f_id, e.e_payload_t_id
FROM node n, edge e
WHERE n.h_id=?
AND n.nt_id=?
AND e.h_id = n.h_id
'''
			params = [hId.h_id, ntId.nt_id]
			
			if (internal_ids is not None) and len(internal_ids) > 0:
				if len(internal_ids) == 1:
					query += ' AND n.n_id=?'
				else:
					query += f' AND n.n_id IN ({",".join(["?"] * len(internal_ids))})'
				params.extend(internal_ids)
				
			if (names is not None) and len(names) > 0:
				if len(names) == 1:
					query += ' AND n.n_payload_name=?'
				else:
					query += f' AND n.n_payload_name IN ({",".join(["?"] * len(names))})'
				params.extend(names)
				
			if (_ids is not None) and len(_ids) > 0:
				if len(_ids) == 1:
					query += ' AND n.n_payload_id=?'
				else:
					query += f' AND n.n_payload_id IN ({",".join(["?"] * len(_ids))})'
				params.extend(_ids)
			
			# Additional join conditions
			if from_to:
				query += ' AND n.n_id = e.to_id'
			else:
				query += ' AND n.n_id = e.from_id'
			
			if etId is not None:
				query += ' AND e.et_id = ?'
				params.append(etId.et_id)
			
			for e in cur.execute(query, params):
				cur_et_id = e[1]
				edge = EdgeId(
					e_id=e[0],
					et_id=cur_et_id,
					e_payload_id=e[2],
					weight=e[3],
					from_id=e[4],
					to_id=e[5],
					from_payload_id=e[6],
					to_payload_id=e[7]
				)
				retval_et = retval_batches.get(cur_et_id)
				if retval_et is None:
					curEtId = self.cachedEdgeTypesByInternalId.get(cur_et_id)
					retval_batches[cur_et_id] = ( [ edge ], curEtId.name )
				else:
					retval_et[0].append(edge)
			cur.close()
		
		return retval_batches.values()
	
	def getNodesEdgesByGraphAndNode(self, h_payload_id: HypergraphPayloadId, 
	nodeTypeName: NodeTypeName, from_to: bool, edgeTypeName: Optional[EdgeTypeName] = None, 
	names: Optional[List[NodePayloadName]] = None, _ids: Optional[List[NodePayloadId]] = None, 
	internal_ids: Optional[List[InternalNodeId]] = None) -> Iterable[Tuple[List[NodeId], NodeTypeName]]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateNodeTypesCache()
		ntId = self.cachedNodeTypesByName.get(nodeTypeName)
		if ntId is None:
			return None
		
		self._populateEdgeTypesCache()
		etId = None
		if edgeTypeName is not None:
			etId = self.cachedEdgeTypesByName.get(edgeTypeName)
			if etId is None:
				return None
		
		retval_batches = {}
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT nr.n_id, nr.nt_id, nr.n_payload_id, nr.n_payload_name
FROM node n, edge e, node nr
WHERE n.h_id=?
AND n.nt_id=?
AND e.h_id = n.h_id
'''
			params = [hId.h_id, ntId.nt_id]
			
			if (internal_ids is not None) and len(internal_ids) > 0:
				if len(internal_ids) == 1:
					query += ' AND n.n_id=?'
				else:
					query += f' AND n.n_id IN ({",".join(["?"] * len(internal_ids))})'
				params.extend(internal_ids)
				
			if (names is not None) and len(names) > 0:
				if len(names) == 1:
					query += ' AND n.n_payload_name=?'
				else:
					query += f' AND n.n_payload_name IN ({",".join(["?"] * len(names))})'
				params.extend(names)
				
			if (_ids is not None) and len(_ids) > 0:
				if len(_ids) == 1:
					query += ' AND n.n_payload_id=?'
				else:
					query += f' AND n.n_payload_id IN ({",".join(["?"] * len(_ids))})'
				params.extend(_ids)
				
			# Additional join conditions
			if from_to:
				query += ' AND n.n_id = e.to_id AND e.from_id = nr.n_id'
			else:
				query += ' AND n.n_id = e.from_id AND e.to_id = nr.n_id'
			
			if etId is not None:
				query += ' AND e.et_id = ?'
				params.append(etId.et_id)
			
			# A set is internally used to skip duplicate
			# results, because SELECT DISTINCT is not so
			# optimized in SQLite
			n_id_set = set()
			for n in cur.execute(query, params):
				cur_n_id = n[0]
				if cur_n_id  in n_id_set:
					continue
				n_id_set.add(cur_n_id)
				cur_nt_id = n[1]
				node = NodeId(
					n_id=n[0],
					nt_id=cur_nt_id,
					n_payload_id=n[2],
					n_payload_name=n[3],
				)
				retval_nt = retval_batches.get(cur_nt_id)
				if retval_nt is None:
					curNtId = self.cachedNodeTypesByInternalId.get(cur_nt_id)
					retval_batches[cur_nt_id] = ( [ node ], curNtId.name )
				else:
					retval_nt[0].append(node)
			cur.close()
		
		return retval_batches.values()
	
	def getHyperedgesByGraphAndNode(self, h_payload_id: HypergraphPayloadId, 
		nodeTypeName: NodeTypeName, hyperedgeTypeName: Optional[HyperedgeTypeName] = None, 
		names: Optional[List[NodePayloadName]] = None, _ids: Optional[List[NodePayloadId]] = None, 
		internal_ids: Optional[List[InternalNodeId]] = None) -> Iterable[Tuple[List[HyperedgeId], 
		HyperedgeTypeName]]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateNodeTypesCache()
		ntId = self.cachedNodeTypesByName.get(nodeTypeName)
		if ntId is None:
			return None
		
		self._populateHyperedgeTypesCache()
		hetId = None
		if hyperedgeTypeName is not None:
			hetId = self.cachedHyperedgeTypesByName.get(hyperedgeTypeName)
			if hetId is None:
				return None
		
		retval_batches = {}
		retvalH = {}
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT he.he_id, he.het_id, he.he_payload_id, he.he_payload_weight, he_nr.n_id, nr.n_payload_id
FROM node n, hyperedge he, hyperedge_node he_n, hyperedge_node he_nr, node nr
WHERE n.h_id=?
AND n.nt_id=?
AND he.h_id = n.h_id
AND he.h_id = nr.h_id
AND he.he_id = he_n.he_id
AND he_n.n_id = n.n_id
AND he.he_id = he_nr.he_id
AND he_nr.n_id = nr.n_id
'''
			params = [hId.h_id, ntId.nt_id]
			
			# Additional join conditions
			if hetId is not None:
				query += ' AND he.het_id = ?'
				params.append(hetId.het_id)
			
			if (internal_ids is not None) and len(internal_ids) > 0:
				if len(internal_ids) == 1:
					query += ' AND n.n_id=?'
				else:
					query += f' AND n.n_id IN ({",".join(["?"] * len(internal_ids))})'
				params.extend(internal_ids)
				
			if (names is not None) and len(names) > 0:
				if len(names) == 1:
					query += ' AND n.n_payload_name=?'
				else:
					query += f' AND n.n_payload_name IN ({",".join(["?"] * len(names))})'
				params.extend(names)
				
			if (_ids is not None) and len(_ids) > 0:
				if len(_ids) == 1:
					query += ' AND n.n_payload_id=?'
				else:
					query += f' AND n.n_payload_id IN ({",".join(["?"] * len(_ids))})'
				params.extend(_ids)
				
			# This is needed to assure the nodes appear in
			# the same order they were stored related to the
			# hyperedge
			for he in cur.execute(query + ' ORDER BY he_nr.he_n_id', params):
				cur_he_id = he[0]
				edge = retvalH.get(cur_he_id)
				if edge is None:
					cur_het_id = he[1]
					hyperedge = HyperedgeId(
						he_id=he[0],
						het_id=cur_het_id,
						he_payload_id=he[2],
						weight=he[3],
						n_ids=[ he[4] ],
						n_payload_ids=[ he[5] ],
					)
					retvalH[cur_he_id] = hyperedge
					
					retval_het = retval_batches.get(cur_het_id)
					if retval_het is None:
						curHetId = self.cachedHyperedgeTypesByInternalId.get(cur_het_id)
						retval_batches[cur_het_id] = ( [ hyperedge ], curHetId.name )
					else:
						retval_het[0].append(hyperedge)
				else:
					hyperedge.n_ids.append(he[4])
					hyperedge.n_payload_ids.append(he[5])
			
			cur.close()
		
		return retval_batches.values()
	
	def getNodesHyperedgesByGraphAndNode(self, h_payload_id: HypergraphPayloadId, nodeTypeName: NodeTypeName, 
		hyperedgeTypeName: Optional[HyperedgeTypeName] = None, names: Optional[List[NodePayloadName]] = None, _ids: Optional[List[NodePayloadId]] = None, internal_ids: Optional[List[InternalNodeId]] = None) -> Iterable[Tuple[List[NodeId], NodeTypeName]]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateNodeTypesCache()
		ntId = self.cachedNodeTypesByName.get(nodeTypeName)
		if ntId is None:
			return None
		
		self._populateHyperedgeTypesCache()
		hetId = None
		if hyperedgeTypeName is not None:
			hetId = self.cachedHyperedgeTypesByName.get(hyperedgeTypeName)
			if hetId is None:
				return None
		
		retval_batches = {}
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT nr.n_id, nr.nt_id, nr.n_payload_id, nr.n_payload_name
FROM node n, hyperedge he, hyperedge_node he_n, hyperedge_node he_nr, node nr
WHERE n.h_id=?
AND n.nt_id=?
AND he.h_id = n.h_id
AND he.h_id = nr.h_id
AND he.he_id = he_n.he_id
AND he_n.n_id = n.n_id
AND he.he_id = he_nr.he_id
AND he_nr.n_id = nr.n_id
'''
			params = [hId.h_id, ntId.nt_id]
			
			# Additional join conditions
			if hetId is not None:
				query += ' AND he.het_id = ?'
				params.append(hetId.het_id)
			
			if (internal_ids is not None) and len(internal_ids) > 0:
				if len(internal_ids) == 1:
					query += ' AND n.n_id=?'
				else:
					query += f' AND n.n_id IN ({",".join(["?"] * len(internal_ids))})'
				params.extend(internal_ids)
				
			if (names is not None) and len(names) > 0:
				if len(names) == 1:
					query += ' AND n.n_payload_name=?'
				else:
					query += f' AND n.n_payload_name IN ({",".join(["?"] * len(names))})'
				params.extend(names)
				
			if (_ids is not None) and len(_ids) > 0:
				if len(_ids) == 1:
					query += ' AND n.n_payload_id=?'
				else:
					query += f' AND n.n_payload_id IN ({",".join(["?"] * len(_ids))})'
				params.extend(_ids)
			
			# A set is internally used to skip duplicate
			# results, because SELECT DISTINCT is not so
			# optimized in SQLite
			n_id_set = set()
			# This is needed to assure the nodes appear in
			# the same order they were stored related to the
			# hyperedge
			for n in cur.execute(query + ' ORDER BY he_nr.he_id, he_nr.he_n_id', params):
				cur_n_id = n[0]
				if cur_n_id in n_id_set:
					continue
				
				n_id_set.add(cur_n_id)
				cur_nt_id = n[1]
				node = NodeId(
					n_id=n[0],
					nt_id=cur_nt_id,
					n_payload_id=n[2],
					n_payload_name=n[3],
				)
				retval_nt = retval_batches.get(cur_nt_id)
				if retval_nt is None:
					curNtId = self.cachedNodeTypesByInternalId.get(cur_nt_id)
					retval_batches[cur_nt_id] = ( [ node ], curNtId.name )
				else:
					retval_nt[0].append(node)
			cur.close()
		
		return retval_batches.values()
	
	def registeredEdges(self, cur: sqlite3.Cursor, hId: InternalHypergraphId, etId: Union[InternalEdgeTypeId, List[InternalEdgeTypeId]]) -> List[EdgeId]:
		"""
		Retrieves the list of known edges from this hypergraph
		"""
		retval = []
		if not isinstance(etId, (list, tuple)):
			etId = [ etId ]
		with self.conn:
			cur = self.conn.cursor()
			for e in cur.execute(f'SELECT e_id, et_id, e_payload_id, from_id, to_id FROM edge WHERE h_id=? AND et_id IN ({",".join(["?"]*len(etId))})', (hId, *etId)):
				retval.append(EdgeId(e_id=e[0], et_id=e[1], e_payload_id=e[2], from_id=e[3], to_id=e[4]))
			cur.close()
		
		return retval
	
	def registeredEdgesByGraphAndEdgeType(self, h_payload_id: HypergraphPayloadId, 
		edgeTypeName: EdgeTypeName) -> List[EdgeId]:
		"""
		Retrieves the list of known edges from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateEdgeTypesCache()
		etId = self.cachedEdgeTypesByName.get(edgeTypeName)
		if etId is None:
			return None
		
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			query = 'SELECT e_id, et_id, e_payload_id, e_payload_weight, from_id, to_id, e_payload_f_id, e_payload_t_id FROM edge WHERE h_id=? AND et_id=?'
			params = [hId.h_id, etId.et_id]
			for e in cur.execute(query, params):
				retval.append(EdgeId(
					e_id=e[0],
					et_id=e[1],
					e_payload_id=e[2],
					weight=e[3],
					from_id=e[4],
					to_id=e[5],
					from_payload_id=e[6],
					to_payload_id=e[7]
				))
			cur.close()
		
		return retval
	
	def getEdgesByGraphAndEdgeType(self, h_payload_id: HypergraphPayloadId, edgeTypeName: EdgeTypeName, internal_id: Optional[InternalEdgeId] = None, _id: Optional[EdgePayloadId] = None) -> List[EdgeId]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateEdgeTypesCache()
		etId = self.cachedEdgeTypesByName.get(edgeTypeName)
		if etId is None:
			return None
		
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			query = 'SELECT e_id, et_id, e_payload_id, e_payload_weight, from_id, to_id, e_payload_f_id, e_payload_t_id, payload FROM edge WHERE h_id=? AND et_id=?'
			params = [hId.h_id, etId.et_id]
			if internal_id is not None:
				query += ' AND e_id=?'
				params.append(internal_id)
			if _id is not None:
				query += ' AND e_payload_id=?'
				params.append(_id)
			for e in cur.execute(query, params):
				retval.append(EdgeId(
					e_id=e[0],
					et_id=e[1],
					e_payload_id=e[2],
					weight=e[3],
					from_id=e[4],
					to_id=e[5],
					from_payload_id=e[6],
					to_payload_id=e[7],
					payload=None if e[8] is None else json.loads(e[8])
				))
			cur.close()
		
		return retval
	
	def getNodesByGraphAndEdge(self, h_payload_id: HypergraphPayloadId, edgeTypeName: EdgeTypeName, from_to: bool, internal_id: Optional[InternalEdgeId] = None, _id: Optional[EdgePayloadId] = None) -> Tuple[List[NodeId], NodeTypeName]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None, None
		
		self._populateEdgeTypesCache()
		etId = self.cachedEdgeTypesByName.get(edgeTypeName)
		if etId is None:
			return None, None
		
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT n.n_id, n.nt_id, n.n_payload_id, n.n_payload_name
FROM edge e, node n
WHERE e.h_id=?
AND e.et_id=?
'''
			params = [hId.h_id, etId.et_id]
			if internal_id is not None:
				query += ' AND e.e_id=?'
				params.append(internal_id)
			if _id is not None:
				query += ' AND e.e_payload_id=?'
				params.append(_id)
			
			if from_to:
				ntId = etId.to_type
				query += ' AND n.n_id = e.to_id'
			else:
				ntId = etId.from_type
				query += ' AND n.n_id = e.from_id'
			
			for n in cur.execute(query, params):
				retval.append(NodeId(
					n_id=n[0],
					nt_id=n[1],
					n_payload_id=n[2],
					n_payload_name=n[3],
				))
			cur.close()
		
		return retval, ntId.name
	
	def registeredHyperedges(self, cur: sqlite3.Cursor, hId: InternalHypergraphId, 
		hetId: Union[InternalHyperedgeTypeId, List[InternalHyperedgeTypeId]]) -> List[HyperedgeId]:
		"""
		Retrieves the list of known hyperedges from this hypergraph
		"""
		retval = []
		retHash = {}
		if not isinstance(hetId, (list, tuple)):
			hetId = [ hetId ]
		for he in cur.execute(f'SELECT he.he_id, he.het_id, he.he_payload_id, hen.n_id FROM hyperedge he, hyperedge_node hen WHERE he.h_id=? AND he.het_id IN ({",".join(["?"]*len(hetId))}) AND he.he_id = hen.he_id', (hId, *hetId)):
			if he[0] in retHash:
				heId = retHash[he[0]]
				heId.n_id.append(he[3])
			else:
				heId = HyperedgeId(he_id=he[0], het_id=he[1], he_payload_id=he[2], n_id=[he[3]]) 
				retHash[he[0]] = heId
				retval.append(heId)
		
		return retval
	
	def registeredHyperedgesByGraphAndHyperedgeType(self, h_payload_id: HypergraphPayloadId, 
		hyperedgeTypeName: HyperedgeTypeName) -> List[HyperedgeId]:
		"""
		Retrieves the list of known edges from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateHyperedgeTypesCache()
		hetId = self.cachedHyperedgeTypesByName.get(hyperedgeTypeName)
		if hetId is None:
			return None
		
		retval = []
		retvalHash = {}
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT he.he_id, he.het_id, he.he_payload_id, he.he_payload_weight, he_n.n_id, n.n_payload_id
FROM hyperedge he, hyperedge_node he_n, node n
WHERE he.h_id=?
AND he.het_id=?
AND he.he_id = he_n.he_id
AND he_n.n_id = n.n_id
ORDER BY he_n.he_n_id
'''
			params = [hId.h_id, hetId.het_id]
			for e in cur.execute(query, params):
				eId = retvalHash.get(e[0])
				if eId is None:
					eId = EdgeId(
						e_id=e[0],
						et_id=e[1],
						he_payload_id=e[2],
						weight=e[3],
						n_ids=[ e[4] ],
						n_payload_ids=[ e[5] ],
					)
					retval.append(eId)
					retvalHash[e[0]] = eId
				else:
					eId.n_ids.append(e[4])
					eId.n_payload_ids.append(e[5])
			cur.close()
		
		return retval
	

	def getEdgesByEdgeAndNodesIds(self, h_payload_id: HypergraphPayloadId, _ids: List[NodePayloadId],
		edgeTypeNameRetrieve: EdgeTypeName, edges_conection: List[EdgeTypeName], min_size: Optional[int]= None):
		""",
		Retrieve the list of edges of the given type connected through edges way to the given node ids 
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None

		retval = []
		with self.conn:
			cur = self.conn.cursor()
			queryDrop = "DROP TABLE prueba"

			if (min_size):
				queryTmpTable = '''
	CREATE TABLE prueba AS
	SELECT n_d.*, c.num
	FROM edge e, edge_type et, node n_o, node n_d,
	(
			SELECT from_id, count(*) as num
			FROM edge_type
			JOIN edge ON edge_type.et_id=edge.et_id
			WHERE et_name =?
			GROUP BY 1
	) c
	WHERE et.et_name =?
	AND n_o.h_id=?
	AND e.et_id = et.et_id
	AND n_o.n_id = e.from_id
	AND e.to_id = n_d.n_id
	AND e.to_id = c.from_id
	AND c.num > ?
	'''	
				query = '''
SELECT e_x.*, c_f.num, c_t.num
FROM edge e_x, edge_type et_x, prueba c_f, prueba c_t
WHERE et_x.et_name =?
AND e_x.et_id = et_x.et_id
AND e_x.from_id = c_f.n_id
AND e_x.to_id = c_t.n_id;
'''				
				queryTmpTableParams= [edges_conection[1], edges_conection[0], hId.h_id, min_size]
				queryTmpTableParams.extend(_ids)
				queryTmpTable += f' AND n_o.n_payload_id IN ({",".join(["?"] * len(_ids))})'

			else:
				queryTmpTable = '''
	CREATE TABLE prueba AS
	SELECT n_d.*
	FROM edge e, edge_type et, node n_o, node n_d
	WHERE et.et_name =?
	AND n_o.h_id=?
	AND e.et_id = et.et_id
	AND n_o.n_id = e.from_id
	AND e.to_id = n_d.n_id
	'''
				query = '''
SELECT e_x.*
FROM edge e_x, edge_type et_x, prueba c_f, prueba c_t
WHERE et_x.et_name =?
AND e_x.et_id = et_x.et_id
AND e_x.from_id = c_f.n_id
AND e_x.to_id = c_t.n_id;
'''				
				queryTmpTableParams= [edges_conection[0], hId.h_id]
				queryTmpTableParams.extend(_ids)
				queryTmpTable += f' AND n_o.n_payload_id IN ({",".join(["?"] * len(_ids))})'
			
			queryIndex = "CREATE UNIQUE INDEX prueba_1 ON prueba(n_id);"
			queryParams = [edgeTypeNameRetrieve]
			print(queryTmpTable)
			print(queryTmpTableParams)
			#execute queries
			try:
				cur.execute(queryTmpTable, queryTmpTableParams)
				cur.execute(queryIndex)
				
				for e in cur.execute(query, queryParams):
					retval.append(EdgeId(
						e_id=e[0],
						et_id=e[2],
						e_payload_id=e[9],
						weight=e[10],
						from_id=e[3],
						to_id=e[4],
						from_payload_id=e[7],
						to_payload_id=e[8],
						payload = e[6]
					))
			finally: 
				cur.execute(queryDrop)
				cur.close()
				
		return retval


	def getNodesByEdgesAndNodesIds(self, h_payload_id: HypergraphPayloadId, _ids: List[NodePayloadId],
		nodeTypeNameRetrieve: NodeTypeName, edges_conection: List[EdgeTypeName]):

		"""
		Retrieve the list of nodes of the given type conected to the given node ids 
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None

		retval = []
		with self.conn:
			cur = self.conn.cursor()
			queryDrop = "DROP TABLE prueba2"
			queryTmpTable = '''
CREATE TEMP TABLE prueba2 AS
SELECT n_d.*
FROM edge e, edge_type et, node n_o, node n_d
WHERE n_o.h_id=?
AND et.et_name =?
AND e.et_id = et.et_id
AND n_o.n_id = e.from_id
AND e.to_id = n_d.n_id

'''
			
			queryIndex = "CREATE UNIQUE INDEX prueba_1 ON prueba2(n_id);"
			query = '''
SELECT DISTINCT n.n_id, n.nt_id, n.n_payload_id, n.n_payload_name
FROM node n, node_type nt, edge e_x, edge_type et_x, prueba2 c_f
WHERE et_x.et_name =?
AND e_x.et_id = et_x.et_id
AND e_x.from_id = c_f.n_id
AND n.nt_id=nt.nt_id
AND nt.nt_name =?
AND n.n_id= e_x.to_id;
'''

			queryTmpTableParams= [hId.h_id]
			queryTmpTableParams.append(edges_conection[0])
			queryTmpTable += f' AND n_o.n_payload_id IN ({",".join(["?"] * len(_ids))})'
			queryTmpTableParams.extend(_ids)
			
			queryParams = [edges_conection[1], nodeTypeNameRetrieve]
			
			#execute queries
			try: 
				cur.execute(queryTmpTable, queryTmpTableParams)
				cur.execute(queryIndex)
				
				for n in cur.execute(query, queryParams):
					retval.append(NodeId(
						n_id=n[0],
						nt_id=n[1],
						n_payload_id=n[2],
						n_payload_name=n[3]
					))
			finally: 
				cur.execute(queryDrop)
				cur.close()
				
		return retval
		
		
	def getHyperedgesByGraphAndHyperedgeType(self, h_payload_id: HypergraphPayloadId, 
		hyperedgeTypeName: HyperedgeTypeName, internal_id: Optional[InternalHyperedgeId] = None, 
		_id: Optional[EdgePayloadId] = None) -> List[HyperedgeId]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None
		
		self._populateHyperedgeTypesCache()
		hetId = self.cachedHyperedgeTypesByName.get(hyperedgeTypeName)
		if hetId is None:
			return None
		
		retval = []
		retvalHash = {}
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT he.he_id, he.het_id, he.he_payload_id, he.he_payload_weight, he_n.n_id, n.n_payload_id, he.payload
FROM hyperedge he, hyperedge_node he_n, node n
WHERE he.h_id=?
AND he.het_id=?
AND he.he_id = he_n.he_id
AND he_n.n_id = n.n_id
'''
			params = [hId.h_id, hetId.het_id]
			if internal_id is not None:
				query += ' AND he.he_id=?'
				params.append(internal_id)
			if _id is not None:
				query += ' AND he.he_payload_id=?'
				params.append(_id)
			for he in cur.execute(query + ' ORDER BY he_n.he_n_id', params):
				heId = retvalHash.get(he[0])
				if heId is None:
					heId = HyperedgeId(
						he_id=he[0],
						het_id=he[1],
						he_payload_id=he[2],
						weight=he[3],
						n_ids=[ he[4] ],
						n_payload_ids=[ he[5] ],
						payload=None if he[6] is None else json.loads(he[6])
					)
					retval.append(heId)
					retvalHash[he[0]] = heId
				else:
					heId.n_ids.append(he[4])
					heId.n_payload_ids.append(he[5])
			cur.close()
		
		return retval
	

	def getNodesByGraphAndHyperedge(self, h_payload_id: HypergraphPayloadId, hyperedgeTypeName: HyperedgeTypeName, internal_id: Optional[InternalHyperedgeId] = None, _id: Optional[HyperedgePayloadId] = None) -> Iterable[Tuple[NodeId, NodeTypeName]]:
		"""
		Retrieves the list of known nodes from this hypergraph
		"""
		self._populateHypergraphsCache()
		hId = self.cachedHypergraphs.get(h_payload_id)
		if hId is None:
			return None, None
		
		self._populateHyperedgeTypesCache()
		hetId = self.cachedHyperedgeTypesByName.get(hyperedgeTypeName)
		if hetId is None:
			return None, None
		
		self._populateNodeTypesCache()
		retval = []
		with self.conn:
			cur = self.conn.cursor()
			query = '''
SELECT nr.n_id, nr.nt_id, nr.n_payload_id, nr.n_payload_name
FROM hyperedge he, hyperedge_node he_n, node nr
WHERE he.h_id=?
AND he.het_id=?
AND he.he_id = he_n.he_id
AND he_n.n_id = nr.n_id
AND he.h_id = nr.h_id
'''
			params = [hId.h_id, hetId.het_id]
			if internal_id is not None:
				query += ' AND he.he_id=?'
				params.append(internal_id)
			if _id is not None:
				query += ' AND he.he_payload_id=?'
				params.append(_id)
			
			for n in cur.execute(query + ' ORDER BY he_n.he_n_id', params):
				nt_id = n[1]
				node = NodeId(
					n_id=n[0],
					nt_id=nt_id,
					n_payload_id=n[2],
					n_payload_name=n[3],
				)
				ntId = self.cachedNodeTypesByInternalId[nt_id]
				retval.append( (node, ntId.name) )
			cur.close()
		
		return retval
	
	def registeredHypergraphs(self, cur: sqlite3.Cursor) -> List[HypergraphId]:
		"""
		Retrieves the list of known hypergraphs
		"""
		retval = []
		for h in cur.execute('SELECT h_id, stored_at, updated_at, h_payload_id FROM hypergraph'):
			retval.append(HypergraphId(h_id=h[0], stored_at=h[1], updated_at=h[2], h_payload_id=h[3]))
			
		return retval
	
	def getNodeByGraphAndId(self, hId: InternalHypergraphId, nodeId: NodePayloadId) -> Tuple[InternalNodeId, InternalNodeTypeId, Any]:
		"""
		This method returns both the internal node id and
		the node payload
		"""
		with self.conn:
			cur = self.conn.cursor()
			for n in cur.execute('SELECT n_id, nt_id, payload FROM node WHERE h_id = ? AND n_payload_id = ?', (hId, nodeId)):
				return n[0], n[1], json.loads(n[2])
		
		return None, None, None
	
	def getNodeByInternalId(self, cur: sqlite3.Cursor, internalNodeId: InternalNodeId) -> Tuple[InternalNodeTypeId, Any]:
		for n in cur.execute('SELECT nt_id, payload FROM node WHERE n_id = ?', (internalNodeId,)):
			return n[0], json.loads(n[1])
		
		return None, None
	
	def getEdgeByGraphAndId(self, hId: InternalHypergraphId, edgeId: EdgePayloadId) -> Tuple[InternalEdgeId, InternalEdgeTypeId, Any]:
		"""
		This method returns both the internal edge id and
		the edge payload
		"""
		with self.conn:
			cur = self.conn.cursor()
			for e in cur.execute('SELECT e_id, et_id, payload FROM edge WHERE h_id = ? AND e_payload_id = ?', (hId, edgeId)):
				return e[0], e[1], json.loads(e[2])
		
		return None, None, None
	
	def getEdgeByInternalId(self, cur: sqlite3.Cursor, internalEdgeId: InternalEdgeId) -> Tuple[InternalEdgeTypeId, Any]:
		for e in cur.execute('SELECT et_id, payload FROM edge WHERE e_id = ?', (internalEdgeId,)):
			return e[0], json.loads(e[1])
		
		return None, None
	
	def getHyperedgeByGraphAndId(self, hId: InternalHypergraphId, heId: HyperedgePayloadId) -> Tuple[InternalHyperedgeId, InternalHyperedgeTypeId, Any]:
		"""
		This method returns both the internal hyperedge id and
		the hyperedge payload
		"""
		with self.conn:
			cur = self.conn.cursor()
			for he in cur.execute('SELECT he_id, het_id, payload FROM hyperedge WHERE h_id = ? AND he_payload_id = ?', (hId, heId)):
				return he[0], he[1], json.loads(he[2])
		
		return None, None, None
	
	def getHyperedgeByInternalId(self, cur: sqlite3.Cursor, internalHyperedgeId: InternalHyperedgeId) -> Tuple[InternalHyperedgeTypeId, Any]:
		for he in cur.execute('SELECT het_id, payload FROM hyperedge WHERE he_id = ?', (internalHyperedgeId,)):
			return he[0], json.loads(he[1])
		
		return None, None
	
	def _store_hypergraph_metadata(self, cur: sqlite3.Cursor, hm: Mapping[str, Any], hypergraphMetaFilename: str) -> InternalHypergraphId:
		hmSchemaId = hm.get('_schema')
		if hmSchemaId is None:
			raise HypergraphsStoreException(f"Hypergraph metadata file {hypergraphMetaFilename} does not indicate its JSON Schema")
		
		
		hmsV = self.getJSONSchemaValidator(hmSchemaId)
		if hmsV is None:
			raise HypergraphsStoreException(f"JSON Schema {hmSchemaId}, needed by {hypergraphMetaFilename}, is not in the database. Did you mispelled it?")
		h_errors = list(hmsV.iter_errors(instance=hm))
		if len(h_errors) > 0:
			errmsg = f'Hypergraph {hypergraphMetaFilename} validation errors: {h_errors}'
			for iErr, h_error in enumerate(h_errors):
				self.logger.error(f'ERROR {iErr} in hypergraph metadata: {h_error}')
			raise HypergraphsStoreException(errmsg)
		
		# Last, store it!
		hId = None
		# First, remove previous version of this hypergraph
		prev = self.getHypergraphMetadataId(hm['_id'])
				
		# Now, adding the metadata
		if prev is not None:
			prevHId = prev.h_id
			stored_at = prev.stored_at
			self.logger.info(f"Removing hypergraph {prevHId}")
			self._invalidateHypergraphsCache()
			try:
				cur.execute('DELETE FROM hyperedge WHERE h_id=?', (prevHId,))
				cur.execute('DELETE FROM edge WHERE h_id=?', (prevHId,))
				cur.execute('DELETE FROM node WHERE h_id=?', (prevHId,))
				cur.execute('DELETE FROM hypergraph WHERE h_id=?', (prevHId,))
			except Exception as e:
				errmsg = f'Error while removing previous hypergraph version {prevHId}'
				self.logger.exception(errmsg)
				raise HypergraphsStoreException(errmsg)
		else:
			stored_at = None
		
		try:
			cur.execute(f'INSERT INTO hypergraph(stored_at, payload) VALUES (?, ?)', (stored_at, json.dumps(hm, sort_keys=True),))
			hId = cur.lastrowid
		except Exception as e:
			errmsg = 'Error while loading new hypergraph metadata'
			self.logger.exception(errmsg)
			raise HypergraphsStoreException(errmsg)
		
		self.logger.debug(f"Hypergraph id {hId}")
		
		return hId
	
	import gzip
	import lzma
	import bz2
	MIME_OPENER = {
		'application/x-xz': lzma.open,
		'application/gzip': gzip.open,
		'application/x-bzip2': bz2.open,
	}
	
	def _detect_opener(self, hBasePath, data_filename):
		if not os.path.isabs(data_filename):
			data_filename = os.path.normpath(os.path.join(hBasePath, data_filename))
		
		if not os.path.exists(data_filename):
			errmsg = f"Data file {data_filename} is not available"
			self.logger.error(errmsg)
			raise HypergraphsStoreException(errmsg)
		
		data_mime = filetype.guess_mime(data_filename)
		self.logger.debug(f'Guess mime {data_mime} for data file {data_filename}')
		opener = self.MIME_OPENER.get(data_mime, open)
		
		return data_filename , opener
	
	def _classify_mappings(self, hBasePath, datafiles: List[Any]) -> int:
		mappingTuples = {}
		mappingHashes = {
			'node': {
				nt.name: nt
				for nt in self.registeredNodeTypes()
			},
			'edge': {
				et.name: et
				for et in self.registeredEdgeTypes()
			},
			'hyperedge': {
				het.name: het
				for het in self.registeredHyperedgeTypes()
			}
		}
		
		for datafile in datafiles:
			data_filename , opener = self._detect_opener(hBasePath, datafile['file'])
			for mapping in datafile['maps']:
				mappingClass = mapping['class']
				mappingType = mapping['type']
				
				mT = mappingHashes[mappingClass].get(mappingType)
				if mT is None:
					errmsg = f'{mappingClass} type {mappingType} is not available in database'
					self.logger.error(errmsg)
					raise HypergraphsStoreException(errmsg)
				
				mappingTuples.setdefault(mappingClass, []).append( (data_filename, opener, mapping, mT) )
		
		return mappingTuples
	
	def _store_node(self, cur: sqlite3.Cursor, hId: InternalHypergraphId, ntId: InternalNodeTypeId, payload: Any) -> InternalNodeId:
		# Last, store it!
		nId = None
		pStr = json.dumps(payload, sort_keys=True)
		try:
			cur.execute(f'INSERT INTO node(h_id, nt_id, payload) VALUES (?, ?, ?)', (hId, ntId, pStr,))
			nId = cur.lastrowid
		except Exception as e:
			errmsg = f'Error while loading new node data (payload {pStr})'
			self.logger.exception(errmsg)
			raise HypergraphsStoreException(errmsg)
		
		return nId
		
	def _update_node_payload(self, cur: sqlite3.Cursor, nId: InternalNodeId, payload: Any) -> InternalNodeId:
		# Last, update it!
		pStr = json.dumps(payload, sort_keys=True)
		try:
			cur.execute(f'UPDATE node SET payload = ? WHERE n_id = ?', (pStr, nId, ))
		except Exception as e:
			errmsg = f'Error while updating node payload data (payload {pStr})'
			self.logger.exception(errmsg)
			raise HypergraphsStoreException(errmsg)
		
		return nId
	
	def _store_edge(self, cur: sqlite3.Cursor, hId: InternalHypergraphId, etId: InternalEdgeTypeId, fId: InternalNodeId, tId: InternalNodeId, payload: Any) -> InternalEdgeId:
		# Last, store it!
		eId = None
		pStr = json.dumps(payload, sort_keys=True)
		try:
			cur.execute(f'INSERT INTO edge(h_id, et_id, from_id, to_id, payload) VALUES (?, ?, ?, ?, ?)', (hId, etId, fId, tId, pStr,))
			eId = cur.lastrowid
		except Exception as e:
			errmsg = f'Error while loading new edge data (payload {pStr})'
			self.logger.exception(errmsg)
			raise HypergraphsStoreException(errmsg)
		
		return eId
	
	def _update_edge_payload(self, cur: sqlite3.Cursor, eId: InternalEdgeId, payload: Any) -> InternalEdgeId:
		# Last, update it!
		pStr = json.dumps(payload, sort_keys=True)
		try:
			cur.execute(f'UPDATE edge SET payload = ? WHERE e_id = ?', (pStr, eId, ))
		except Exception as e:
			errmsg = f'Error while updating edge payload data (payload {pStr})'
			self.logger.exception(errmsg)
			raise HypergraphsStoreException(errmsg)
		
		return eId
	
	def _store_hyperedge(self, cur: sqlite3.Cursor, hId: InternalHypergraphId, hetId: InternalEdgeTypeId, nIds: List[NodeId], payload: Any) -> InternalHyperedgeId:
		# Last, store it!
		heId = None
		pStr = json.dumps(payload, sort_keys=True)
		try:
			cur.execute(f'INSERT INTO hyperedge(h_id, het_id, payload) VALUES (?, ?, ?)', (hId, hetId, pStr,))
			heId = cur.lastrowid
			# And, register the nodes in the hyperedge
			cur.executemany('INSERT INTO hyperedge_node(he_id, n_id) VALUES (?,?)', (
				(heId, nodeId.n_id)
				for nodeId in nIds
			))
		except Exception as e:
			errmsg = f'Error while loading new hyperedge data (payload {pStr})'
			self.logger.exception(errmsg)
			raise HypergraphsStoreException(errmsg)
		
		return heId
	
	def _update_hyperedge_payload(self, cur: sqlite3.Cursor, heId: InternalHyperedgeId, payload: Any) -> InternalHyperedgeId:
		# Last, update it!
		pStr = json.dumps(payload, sort_keys=True)
		try:
			cur.execute(f'UPDATE hyperedge SET payload = ? WHERE he_id = ?', (pStr, heId, ))
		except Exception as e:
			errmsg = f'Error while updating hyperedge payload data (payload {pStr})'
			self.logger.exception(errmsg)
			raise HypergraphsStoreException(errmsg)
		
		return heId
	
	def _store_nodes(self, cur: sqlite3.Cursor, hId: int, mappings: List[Any]) -> Tuple[int, int]:
		numNewNodes = 0
		numUpdates = 0
		numFilteredOutLines = 0
		nodeHash = {
			nodeId.n_payload_id: nodeId
			for nodeId in self.registeredNodes(cur, hId)
		}
		for data_filename, opener, mapping, nT  in mappings:
			nsV = self.getJSONSchemaValidator(nT.schema_id)
			if nsV is None:
				raise HypergraphsStoreException(f"JSON Schema {nT.schema_id}, needed by {data_filename}, is not in the database. Did you mispelled it?")
			
			fileNewNodes = 0
			fileUpdates = 0
			ntli = NodeTabLoaderIterator(mapping, nodeHash, data_filename, opener, lambda n_id: self.getNodeByInternalId(cur, n_id))
			for data, join_n_id, _ in iter(ntli):
				# Data validation
				data['_schema'] = nT.schema_id
				n_errors = list(nsV.iter_errors(instance=data))
				if len(n_errors) > 0:
					errmsg = f'Node data from line {ntli.linenumber} in {data_filename} validation errors: {n_errors}'
					self.logger.error(f'ERROR while validating {json.dumps(data)}')
					for iErr, n_error in enumerate(n_errors):
						self.logger.error(f'ERROR {iErr} in node metadata: {n_error}')
					raise HypergraphsStoreException(errmsg)
				
				# It is removed to avoid redundancies
				del data['_schema']
				
				# And now, the data update or insertion
				if join_n_id is not None:
					self._update_node_payload(cur, join_n_id, payload=data)
					fileUpdates += 1
				else:
					nodePayloadId = data['_id']
					nId = self._store_node(cur, hId, nT.nt_id, payload=data)
					
					# Last, but not the least important
					# add a new entry in the hash, for
					# future updates
					
					nodePayloadName = data['name']
					nodeHash[nodePayloadId] = NodeId(n_id=nId, nt_id=nT.nt_id, n_payload_id=nodePayloadId, n_payload_name=nodePayloadName)
					fileNewNodes += 1
			
			self.logger.debug(f'File {data_filename}: {fileNewNodes} new nodes, {fileUpdates} updates, {ntli.filteredOutLines} filtered out lines')
			numNewNodes += fileNewNodes
			numUpdates += fileUpdates
			numFilteredOutLines += ntli.filteredOutLines
			
			del ntli
		
		self.logger.info(f'Node stats: {len(mappings)} mappings, {numNewNodes} new nodes, {numUpdates} updates, {numFilteredOutLines} filtered out lines')
		return numNewNodes, numUpdates
	
	def _store_edges(self, cur, hId, mappings: List[Any]) -> Tuple[int, int]:
		numNewEdges = 0
		numUpdates = 0
		numFilteredOutLines = 0
		# Needed to speed up resolutions
		nodeHash = {
			nodeId.n_payload_id: nodeId
			for nodeId in self.registeredNodes(cur, hId)
		}
		for data_filename, opener, mapping, eT  in mappings:
			esV = self.getJSONSchemaValidator(eT.schema_id)
			if esV is None:
				raise HypergraphsStoreException(f"JSON Schema {eT.schema_id}, needed by {data_filename}, is not in the database. Did you mispelled it?")
			
			edgeHash = None
			fileNewEdges = 0
			fileUpdates = 0
			etli = EdgeTabLoaderIterator(mapping, nodeHash, data_filename, opener, lambda e_id: self.getEdgeByInternalId(cur, e_id))
			if etli.join_id is not None:
				edgeHash = {
					edgeId.e_payload_id: edgeId
					for edgeId in self.registeredEdges(cur, hId, eT.et_id)
				}
				etli.setEdgeHash(edgeHash)
				
			for data, join_e_id, n_internal_ids in iter(etli):
				# Data validation
				data['_schema'] = eT.schema_id
				e_errors = list(esV.iter_errors(instance=data))
				if len(e_errors) > 0:
					errmsg = f'Edge data from line {etli.linenumber} in {data_filename} validation errors: {e_errors}'
					self.logger.error(f'ERROR while validating {json.dumps(data)}')
					for iErr, e_error in enumerate(e_errors):
						self.logger.error(f'ERROR {iErr} in edge metadata: {e_error}')
					raise HypergraphsStoreException(errmsg)
				
				# It is removed to avoid redundancies
				del data['_schema']
				
				# And now, the data update or insertion
				if join_e_id is not None:
					self._update_edge_payload(cur, join_e_id, payload=data)
					fileUpdates += 1
				else:
					eId = self._store_edge(cur, hId, eT.et_id, n_internal_ids[0], n_internal_ids[1], payload=data)
					
					# Last, but not the least important
					# add a new entry in the hash, for
					# future updates
					
					#if edgePayloadId is not None:
					#	edgeHash[edgePayloadId] = EdgeId(
					#		e_id=eId,
					#		et_id=eT.et_id,
					#		from_id=fromInternalId.n_id,
					#		to_id=toInternalId.n_id,
					#		e_payload_id=edgePayloadId
					#	)
					fileNewEdges += 1
			
			self.logger.debug(f'File {data_filename}: {fileNewEdges} new edges, {fileUpdates} updates, {etli.filteredOutLines} filtered out lines')
			numNewEdges += fileNewEdges
			numUpdates += fileUpdates
			numFilteredOutLines += etli.filteredOutLines
			del etli
		
		self.logger.info(f'Edge stats: {len(mappings)} mappings, {numNewEdges} new edges, {numUpdates} updates, {numFilteredOutLines} filtered out lines')
		
		return numNewEdges, numUpdates
	
	def _store_hyperedges(self, cur, hId, mappings: List[Any]) -> Tuple[int, int]:
		numNewHyperedges = 0
		numUpdates = 0
		numFilteredOutLines = 0
		# Needed to speed up resolutions
		nodeHash = {
			nodeId.n_payload_id: nodeId
			for nodeId in self.registeredNodes(cur, hId)
		}
		mappingTypeHashes = {
			'node': {
				nt.name: nt
				for nt in self.registeredNodeTypes()
			},
			'edge': {
				et.name: et
				for et in self.registeredEdgeTypes()
			},
			'hyperedge': {
				het.name: het
				for het in self.registeredHyperedgeTypes()
			}
		}
		for data_filename, opener, mapping, heT  in mappings:
			hesV = self.getJSONSchemaValidator(heT.schema_id)
			if hesV is None:
				raise HypergraphsStoreException(f"JSON Schema {heT.schema_id}, needed by {data_filename}, is not in the database. Did you mispelled it?")
			
			acceptedNodeTypes = self.expectedNodeTypesForHyperedgeType(heT.het_id)
			acceptedNodeTypeIds = set(map(lambda nt: nt.nt_id, acceptedNodeTypes))
			
			edgeHash = None
			heHash = None
			ktHash = None
			fileNewHyperedges = 0
			fileUpdates = 0
			hetli = HyperedgeTabLoaderIterator(mapping, nodeHash, mappingTypeHashes, acceptedNodeTypeIds, data_filename, opener, lambda he_id: self.getHyperedgeByInternalId(cur, he_id))
			if hetli.join_id is None:
				eTids = list(map(lambda kS: kS.keyType.et_id, filter(lambda kS: kS.className == "edge", hetli.keysSources)))
				heTids = list(map(lambda kS: kS.keyType.het_id, filter(lambda kS: kS.className == "hyperedge", hetli.keysSources)))
				if len(eTids) > 0:
					edgeHash = {
						edgeId.e_payload_id: edgeId
						for edgeId in self.registeredEdges(cur, hId, eTids)
					}
				
				if len(heTids) > 0:
					heHash = {
						heId.e_payload_id: heId
						for heId in self.registeredHyperedges(cur, hId, heTids)
					}
				
				ktHash = {
					"node": nodeHash,
					"edge": edgeHash,
					"hyperedge": heHash
				}
				hetli.setKeyTypeHash(ktHash)
			else:
				heHash = {
					heId.e_payload_id: heId
					for heId in self.registeredHyperedges(cur, hId, heT.het_id)
				}
				hetli.setHyperedgeHash(heHash)
			
			for data, join_he_id, internalIds in iter(hetli):
				# Data validation
				data['_schema'] = heT.schema_id
				he_errors = list(hesV.iter_errors(instance=data))
				if len(he_errors) > 0:
					errmsg = f'Hyperedge data from line {hetli.linenumber} in {data_filename} validation errors: {he_errors}'
					self.logger.error(f'ERROR while validating {json.dumps(data)}')
					for iErr, he_error in enumerate(he_errors):
						self.logger.error(f'ERROR {iErr} in edge metadata: {he_error}')
					raise HypergraphsStoreException(errmsg)
				
				# It is removed to avoid redundancies
				del data['_schema']
				
				# And now, the data update or insertion
				if join_he_id is not None:
					self._update_hyperedge_payload(cur, join_he_id, payload=data)
					fileUpdates += 1
				else:
					heId = self._store_hyperedge(cur, hId, heT.het_id, internalIds, payload=data)
					
					fileNewHyperedges += 1
			
			self.logger.debug(f'File {data_filename}: {fileNewHyperedges} new hyperedges, {fileUpdates} updates, {hetli.filteredOutLines} filtered out lines')
			numNewHyperedges += fileNewHyperedges
			numUpdates += fileUpdates
			numFilteredOutLines += hetli.filteredOutLines
		
		self.logger.info(f'Hyperedge stats: {len(mappings)} mappings, {numNewHyperedges} new hyperedges, {numUpdates} updates, {numFilteredOutLines} filtered out lines')
		
		return numNewHyperedges, numUpdates
			
			
	
	def uploadHypergraph(self, hypergraphDesc: Mapping[str, Any], data_manifestBasePath: Optional[str] = None):
		# Validate the hypergraph metadata
		hypergraphMetaFilename = hypergraphDesc['metafile']
		if not os.path.isabs(hypergraphMetaFilename):
			hypergraphMetaFilename = os.path.normpath(os.path.join(data_manifestBasePath, hypergraphMetaFilename))
		
		if not os.path.exists(hypergraphMetaFilename):
			raise HypergraphsStoreException(f"Hypergraph metadata file {hypergraphMetaFilename} does not exist")
		with open(hypergraphMetaFilename, mode="r", encoding="utf-8") as hmS:
			hm = yaml.load(hmS, Loader=YAMLLoader)
		
		with self.conn:
			cur = self.conn.cursor()
			rollback = False
			numLoaded = 0
			
			# Now, adding the metadata
			try:
				hId = self._store_hypergraph_metadata(cur, hm, hypergraphMetaFilename)
				
				# Now, the base directory comes from the hypergraph metadata file
				hBasePath = os.path.dirname(hypergraphMetaFilename)
				
				mappingTuples = self._classify_mappings(hBasePath, hypergraphDesc['datafiles'])
				
				# Let's start processing the nodes from the data files
				numNewNodes, numNodeUpdates = self._store_nodes(cur, hId, mappingTuples.get('node', []))
				
				# And then, the edges from the data files
				numNewEdges, numEdgeUpdates = self._store_edges(cur, hId, mappingTuples.get('edge', []))
				
				# Last, the hyperedges, those "unknown" entities
				numNewHyperedges, numHyperedgeUpdates = self._store_hyperedges(cur, hId, mappingTuples.get('hyperedge', []))
			except HypergraphsStoreException as dpse:
				rollback = True
				raise dpse
			except Exception as e:
				rollback = True
				errmsg = 'Error while loading new hypergraph metadata'
				self.logger.exception(errmsg)
				raise HypergraphsStoreException(errmsg)
			finally:
				if rollback:
					self.conn.rollback()
				else:
					self.conn.commit()
				cur.close()
		
		

LOGGING_FORMAT = '%(asctime)-15s - [%(levelname)s] %(message)s'

if __name__ == "__main__":
	loggingConf = {
		'format': LOGGING_FORMAT,
	}

	logLevel = logging.INFO
	#if args.logLevel:
	#	logLevel = args.logLevel
	loggingConf['level'] = logLevel

	#if args.logFilename is not None:
	#	loggingConf['filename'] = args.logFilename
	##	loggingConf['encoding'] = 'utf-8'

	logging.basicConfig(**loggingConf)
	print(f"SQLite {sqlite3.sqlite_version} JSON support detected: {HypergraphsStore._detect_extensions()}")
	
	if len(sys.argv) > 1:
		dps = HypergraphsStore(sys.argv[1])
		print(f"Store {sys.argv[1]} contains {len(dps.registeredJSONSchemas())} schemas, {len(dps.registeredNodeTypes())} node types and {len(dps.registeredEdgeTypes())} edge types")
		
		if len(sys.argv) > 2:
			print(f"processing metadata manifest {sys.argv[2]}")
			dps.populateManifest(sys.argv[2])
			
			if len(sys.argv) > 3:
				print(f"processing data manifest {sys.argv[3]}")
				dps.populateDataManifest(sys.argv[3])
