#!/usr/bin/env python3

import logging
import os
from typing import Any, List, Mapping, Tuple, Optional , Union

# We have preference for the C based loader and dumper, but the code
# should fallback to default implementations when C ones are not present
import yaml
try:
	from yaml import CLoader as YAMLLoader, CDumper as YAMLDumper
except ImportError:
	from yaml import Loader as YAMLLoader, Dumper as YAMLDumper

# Importing all the common types
from .common import *

class TabLoaderIteratorException(Exception):
	pass

class NodeTabLoaderIterator(object):
	def __init__(self, mapping:Mapping[str, Any], nodeHash: Mapping[str, NodeId], data_filename:str, opener, getByInternalIdMethod):
		self.logger = logging.getLogger(self.__class__.__name__)
		
		self.data_filename = data_filename
		self.mapping = mapping
		self.nodeHash = nodeHash
		self.getByInternalId = getByInternalIdMethod
		self.linenumber = None
		self.dF = opener(self.data_filename, mode='rt', encoding="utf-8")
		
		name2c = self._get_header()
		if name2c is None:
			raise TabLoaderIteratorException(f'File {self.data_filename} does not contain a header (empty or all comments?)')
		
		self.name2c = name2c
		
		# This is the crucial step
		self._validate_mapping()
		
	def __iter__(self):
		# Estamos abriendo el fichero con el encoding 'latin-1'
		# Para text mining lo recomendable es el encoding 'utf-8'
		self.filteredOutLines = 0
		return self
	
	def _split_raw(self, coldataRaw):
		if self.unpackers is None:
			yield coldataRaw
		else:
			coldatas = [ coldataRaw ]
			for unpacker in self.unpackers:
				coldatasNext = []
				splitVal = "".join(self._fill_data(unpacker.splitExp, coldataRaw))
				colNumber = unpacker.colNumber
				for coldataV in coldatas:
					for splitted in coldataV[colNumber].split(splitVal):
						coldataNext = coldataV[:]
						coldataNext[colNumber] = splitted
						coldatasNext.append(coldataNext)
				
				coldatas = coldatasNext
					
			for coldata in coldatas:
				yield coldata
	
	def __next__(self):
		lenName2c = len(self.name2c)
		for line in self.dF:
			self.linenumber += 1
			if line[0] != '#':
				coldataRaw = line.rstrip("\n\r").split("\t")
				if lenName2c != len(coldataRaw):
					errmsg = f'Mismatch in expected number of columns at line {self.linenumber} from {self.data_filename}: {lenName2c} vs {len(coldataRaw)}'
					self.logger.critical(errmsg)
					raise TabLoaderIteratorException(errmsg)
				
				# Splitting evaluation
				for coldata in self._split_raw(coldataRaw):
					# Filtering evaluation
					if (self.filtersInDef is not None) and not self._true_conditions(self.filtersInDef, coldata):
						self.filteredOutLines += 1
						continue
					if (self.filtersOutDef is not None) and self._true_conditions(self.filtersOutDef, coldata):
						self.filteredOutLines += 1
						continue
					
					data, join_n_id, n_internal_ids = self._build_base_data(coldata)
					
					usedColumnsDef = None
					if self.columnsDef is not None:
						usedColumnsDef = self.columnsDef
					elif self.whenDefs is not None:
						for whenDef in self.whenDefs:
							if self._fill_data(whenDef['property'], coldata) == self._fill_data(whenDef['value'], coldata):
								usedColumnDefs = whenDef['mappings']
								break
						else:
							usedColumnsDef = self.defaultDef
					
					if usedColumnsDef is not None:
						for colDef in usedColumnsDef:
							data = self._fill_data(colDef, coldata, skel=data)
					
					return data, join_n_id, n_internal_ids
		
		self.dF.close()
		raise StopIteration
	
	def _get_header(self) -> Tuple[Mapping[str,int], int]:
		name2c = None
		# Getting the header
		self.linenumber = -1
		for line in self.dF:
			self.linenumber += 1
			if line[0] != '#':
				name2c = {
					colname: icol
					for icol, colname in enumerate(line.rstrip("\n\r").split("\t"))
				}
				break
		
		return name2c
	
	TYPECAST = {
		'string': str,
		'number': float,
		'integer': int,
		'boolean': lambda x: x in ('T', 'true', '1', 'True'),
		'null': lambda x: None
	}
	
	def _check_mappings(self, columnsDef: Any, errpostfix: str = 'needed for column definition, is not available in data file columns'):
		if isinstance(columnsDef, dict):
			for key, val in columnsDef.items():
				self._check_mappings(key, errpostfix)
				self._check_mappings(val, errpostfix)
		elif isinstance(columnsDef, (list, tuple)):
			for elem in columnsDef:
				self._check_mappings(elem, errpostfix)
		elif isinstance(columnsDef, str):
			valDefType = columnsDef.split('::',1)
			if valDefType[0][0] != '"' and (valDefType[0] not in self.name2c):
				errmsg = f'{valDefType[0]}, {errpostfix}'
				self.logger.error(errmsg)
				raise TabLoaderIteratorException(errmsg)
			if len(valDefType) > 1 and (valDefType[1] not in self.TYPECAST):
				errmsg = f'{valDefType[0]}, {errpostfix} because there is no typecast to {valDefType[1]}'
				self.logger.error(errmsg)
				raise TabLoaderIteratorException(errmsg)
	
	def _validate_mapping(self) -> Tuple[Optional[List], Optional[List], Optional[List], Optional[List], Optional[List], Optional[List], Optional[List]]:
		mapping = self.mapping
		
		# Check the expected fields are available
		key_id = mapping.get('key')
		if key_id is not None:
			self._check_mappings(key_id, f'to be used as key, is not available in columns from file {self.data_filename}')
			
		
		join_id = mapping.get('join')
		if join_id is not None:
			self._check_mappings(join_id, f'to be used as join key, is not available in columns from file {self.data_filename}')
		
		columnsDef = mapping.get('mappings')
		if columnsDef is not None:
			self._check_mappings(columnsDef, f'needed for data materialization, is not available in columns from file {self.data_filename}')
		
		switchDef = mapping.get('switch')
		whenDefs = None
		defaultDef = None
		if switchDef is not None:
			whenDefs = switchDef.get('when', [])
			for whenDef in whenDefs:
				errmsgPost = f'needed for data materialization in when {whenDef["property"]} = {whenDef["value"]}, is not available in columns from file {self.data_filename}'
				self._check_mappings(whenDef['property'], errmsgPost)
				self._check_mappings(whenDef['value'], errmsgPost)
				self._check_mappings(whenDef['mappings'], errmsgPost)
				
			defaultDef = switchDef.get('default')
			if defaultDef is not None:
				defaultDef = defaultDef['mappings']
				self._check_mappings(defaultDef, f'needed for data materialization in default, is not available in columns from file {self.data_filename}')
		
		filtersInDef = mapping.get('filter_in')
		if filtersInDef is not None:
			self._check_mappings(filtersInDef, f'needed for data filter in, is not available in columns from file {self.data_filename}')
			
		filtersOutDef = mapping.get('filter_out')
		if filtersOutDef is not None:
			self._check_mappings(filtersOutDef, f'needed for data filter out, is not available in columns from file {self.data_filename}')
		
		unpackDefs = mapping.get('unpack')
		if unpackDefs is not None:
			unpackers = []
			for unpackDef in unpackDefs:
				valName = unpackDef['val']
				valCol = self.name2c.get(valName)
				if valCol is None:
					errmsg = f'Unable to unpack column {valName} from file {self.data_filename}, as it does not exist'
					self.logger.error(errmsg)
					raise TabLoaderIteratorException(errmsg)
				splitDef = unpackDef['split']
				self._check_mappings(splitDef, f'needed for data splitting, is not available in columns from file {self.data_filename}')
				unpackers.append(UnpackDef(colNumber=valCol, splitExp=splitDef))
		else:
			unpackers = None
		
		self.key_id = key_id
		self.join_id = join_id
		self.columnsDef = columnsDef
		self.whenDefs = whenDefs
		self.defaultDef = defaultDef
		self.filtersInDef = filtersInDef
		self.filtersOutDef = filtersOutDef
		self.unpackers = unpackers
	
	def _fill_data(self, columnsDef: Any, coldata: List[str], skel : Any = None):
		if isinstance(columnsDef, dict):
			if not isinstance(skel, dict):
				skel = {}
			for key, val in columnsDef.items():
				comp_key = self._fill_data(key, coldata)
				if comp_key in skel:
					prev_val = skel[comp_key]
				else:
					prev_val = {}
				skel[comp_key] = self._fill_data(val, coldata, skel=prev_val)
			
			return skel
		elif isinstance(columnsDef, (list, tuple)):
			if not isinstance(skel, list):
				skel = []
			for elem in columnsDef:
				skel.append(self._fill_data(elem, coldata))
		elif isinstance(columnsDef, str):
			valDefType = columnsDef.split('::',1)
			if valDefType[0][0] == '"':
				skel = valDefType[0][1:-1]
			else:
				skel = coldata[self.name2c[valDefType[0]]]
			if len(valDefType) > 1:
				skel = self.TYPECAST[valDefType[1]](skel)
		else:
			skel = columnsDef
		
		return skel
	
	def _true_conditions(self, columnsDef: Any, coldata: List[str]) -> bool:
		for columnDef in columnsDef:
			for key,val in columnDef.items():
				if self._fill_data(key, coldata) != self._fill_data(val, coldata):
					break
			else:
				return True
		
		return False
	
	def _build_base_data(self, coldata: List[str]) -> Tuple[Any, Union[InternalNodeId, InternalEdgeId, InternalHyperedgeId], Optional[List[Union[InternalNodeId, InternalEdgeId, InternalHyperedgeId]]]]:
		data = None
		join_n_id = None
		# Preparing the data
		if self.key_id is not None:
			nodePayloadId = ''.join(self._fill_data(self.key_id, coldata))
			data = {
				"_id": nodePayloadId,
			}
		elif self.join_id is not None:
			joinPayloadId = ''.join(self._fill_data(self.join_id, coldata))
			joinInternalId = self.nodeHash.get(joinPayloadId)
			if joinInternalId is None:
				errmsg = f'Line {self.linenumber} from {self.data_filename} depends on data with id {joinPayloadId} which is not stored in the database yet (or has wrong identifiers)'
				self.logger.critical(errmsg)
				raise TabLoaderIteratorException(errmsg)
				
			join_n_id = joinInternalId.n_id
			found_nt_id, data = self.getByInternalId(join_n_id)
			if found_nt_id is None:
				errmsg = f'Line {self.linenumber} from {self.data_filename} depends on data which is not findable in the database'
				self.logger.critical(errmsg)
				raise TabLoaderIteratorException(errmsg)
			if joinInternalId.nt_id != found_nt_id:
				errmsg = f'Trying to mix different node types for {joinInternalId.n_id} ({found_nt_id} vs {joinInternalId.nt_id})'
				self.logger.error(errmsg)
				raise TabLoaderIteratorException(errmsg)
		else:
			data = {}
		
		return data, join_n_id, None
	
class EdgeTabLoaderIterator(NodeTabLoaderIterator):
	def __init__(self, mapping:Mapping[str, Any], nodeHash: Mapping[str, NodeId], data_filename:str, opener, getByInternalIdMethod):
		super().__init__(mapping, nodeHash, data_filename, opener, getByInternalIdMethod)
		self.edgeHash = None
	
	def _validate_mapping(self):
		super()._validate_mapping()
		if self.join_id is None:
			# Check the expected fields are available
			from_id = self.mapping.get('key_f')
			if from_id is not None:
				self._check_mappings(from_id, f'to be used as key, is not available in columns from file {self.data_filename}')
			else:
				raise TabLoaderIteratorException('Missing "key_f" in edge declaration. Should have been caught earlier')
				
			# Check the expected fields are available
			to_id = self.mapping.get('key_t')
			if to_id is not None:
				self._check_mappings(to_id, f'to be used as key, is not available in columns from file {self.data_filename}')
			else:
				raise TabLoaderIteratorException('Missing "key_t" in edge declaration. Should have been caught earlier')
		else:
			from_id = None
			to_id = None
		
		self.from_id = from_id
		self.to_id = to_id
	
	def setEdgeHash(self, edgeHash: Mapping[str, EdgeId]):
		self.edgeHash = edgeHash
	
	def _build_base_data(self, coldata: List[str]) -> Tuple[Any, Union[InternalNodeId, InternalEdgeId, InternalHyperedgeId]]:
		data = None
		join_e_id = None
		n_internal_ids = None
		if self.join_id is not None:
			joinPayloadId = ''.join(self._fill_data(self.join_id, coldata))
			joinInternalId = self.edgeHash.get(joinPayloadId)
			if joinInternalId is None:
				errmsg = f'Line {self.linenumber} from {self.data_filename} depends on data with id {joinPayloadId} which is not stored in the database yet (or has wrong identifiers)'
				self.logger.critical(errmsg)
				raise TabLoaderIteratorException(errmsg)
			
			join_e_id = joinInternalId.e_id
			found_et_id, data = self.getByInternalId(join_e_id)
			if found_et_id is None:
				errmsg = f'Line {self.linenumber} from {self.data_filename} depends on data which is not findable in the database'
				self.logger.critical(errmsg)
				raise TabLoaderIteratorException(errmsg)
			if joinInternalId.et_id != found_et_id:
				errmsg = f'Trying to mix different edge types for {joinInternalId.e_id} ({found_et_id} vs {joinInternalId.et_id})'
				self.logger.error(errmsg)
				raise TabLoaderIteratorException(errmsg)
		else:
			fromPayloadId = ''.join(self._fill_data(self.from_id, coldata))
			fromInternalId = self.nodeHash.get(fromPayloadId)
			if fromInternalId is None:
				errmsg = f'Line {self.linenumber} from {self.data_filename} depends on from data which is not stored in the database yet (or has wrong identifiers)'
				self.logger.critical(errmsg)
				raise TabLoaderIteratorException(errmsg)
			
			toPayloadId = ''.join(self._fill_data(self.to_id, coldata))
			toInternalId = self.nodeHash.get(toPayloadId)
			if toInternalId is None:
				errmsg = f'Line {self.linenumber} from {self.data_filename} depends on to data which is not stored in the database yet (or has wrong identifiers)'
				self.logger.critical(errmsg)
				raise TabLoaderIteratorException(errmsg)
			
			data = {
				"f_id": fromPayloadId,
				"t_id": toPayloadId
			}
			n_internal_ids = (fromInternalId.n_id, toInternalId.n_id)
			if self.key_id is not None:
				edgePayloadId = ''.join(self._fill_data(self.key_id, coldata))
				data["_id"] = edgePayloadId
		
		return data, join_e_id, n_internal_ids

class HyperedgeTabLoaderIterator(NodeTabLoaderIterator):
	def __init__(self, mapping:Mapping[str, Any], nodeHash: Mapping[str, NodeId], mappingTypeHashes, acceptedNodeTypeIds, data_filename:str, opener, getByInternalIdMethod):
		self.heHash = None
		self.ktHash = None
		self.mappingTypeHashes = mappingTypeHashes
		self.acceptedNodeTypeIds = acceptedNodeTypeIds
		if nodeHash is not None:
			self.nodeIdHash = {
				nodeId.n_id: nodeId
				for nodeId in nodeHash.values()
			}
		super().__init__(mapping, nodeHash, data_filename, opener, getByInternalIdMethod)
	
	def _validate_mapping(self):
		super()._validate_mapping()
		if self.join_id is None:
			# Check the expected fields are available
			keysDecl = self.mapping.get('keys')
			keysSources = []
			if keysDecl is not None:
				for iKey, keyDecl in enumerate(keysDecl):
					keyType = self.mappingTypeHashes[keyDecl['class']].get(keyDecl['type'])
					if keyType is None:
						raise TabLoaderIteratorException(f'Key {iKey} needs unknown {keyDecl["class"]} type {keyDecl["type"]}')
					
					self._check_mappings(keyDecl['key'], f'to be used as reference key in hyperedge building, is not available in columns from file {self.data_filename}')
					
					keysSources.append(HyperedgeMemberDef(className=keyDecl['class'], keyType=keyType, key=keyDecl['key']))
			else:
				raise TabLoaderIteratorException('Missing "keys" in hyperedge declaration. Should have been caught earlier')
		else:
			keysSources = None
		
		self.keysSources = keysSources
	
	def setHyperedgeHash(self, heHash: Mapping[str, HyperedgeId]):
		self.heHash = heHash
	
	def setKeyTypeHash(self, ktHash: Mapping[str, Mapping[str, Union[NodeId, EdgeId, HyperedgeId]]]):
		self.ktHash = ktHash
	
	def _build_base_data(self, coldata: List[str]) -> Tuple[Any, Union[InternalNodeId, InternalEdgeId, InternalHyperedgeId]]:
		data = None
		join_he_id = None
		internalIds = None
		# Preparing the data
		if self.join_id is not None:
			joinPayloadId = ''.join(self._fill_data(self.join_id, coldata))
			joinInternalId = self.heHash.get(joinPayloadId)
			if joinInternalId is None:
				errmsg = f'Line {self.linenumber} from {self.data_filename} depends on data with id {joinPayloadId} which is not stored in the database yet (or has wrong identifiers)'
				self.logger.critical(errmsg)
				raise TabLoaderIteratorException(errmsg)
			
			found_het_id, data = self.getByInternalId(joinInternalId.he_id)
			if found_het_id is None:
				errmsg = f'Line {self.linenumber} from {self.data_filename} depends on data which is not findable in the database'
				self.logger.critical(errmsg)
				raise TabLoaderIteratorException(errmsg)
			if joinInternalId.het_id != found_het_id:
				errmsg = f'Trying to mix different hyperedge types for {joinInternalId.he_id} ({found_het_id} vs {joinInternalId.het_id})'
				self.logger.error(errmsg)
				raise TabLoaderIteratorException(errmsg)
		else:
			internalIds = []
			for kS in self.keysSources:
				fromPayloadId = ''.join(self._fill_data(kS.key, coldata))
				fromInternalId = self.ktHash[kS.className].get(fromPayloadId)
				if fromInternalId is None:
					errmsg = f'Line {self.linenumber} from {self.data_filename} depends on a {kS.className} with id {fromInternalId} which is not stored in the database yet (or has wrong identifiers)'
					self.logger.critical(errmsg)
					raise TabLoaderIteratorException(errmsg)
				
				# All the types appear as element 1 of the named tuple ids,
				# and as element of the named tuple types
				if fromInternalId[1] != kS.keyType[0]:
					errmsg = f'Line {self.linenumber} from {self.data_filename} depends on {kS.className} {fromPayloadId} from the wrong type ({fromInternalId[1]} vs {kS.keyType[0]} [{kS.keyType.name}])'
					self.logger.critical(errmsg)
					raise TabLoaderIteratorException(errmsg)
				
				# Needed for consistency checks
				if isinstance(fromInternalId, NodeId):
					internalIds.append(fromInternalId)
				elif isinstance(fromInternalId, EdgeId):
					internalIds.append(self.nodeIdHash[fromInternalId.from_id])
					internalIds.append(self.nodeIdHash[fromInternalId.to_id])
				elif isinstance(fromInternalId, HyperedgeId):
					internalIds.extend(map(lambda n_id: self.nodeIdHash[n_id], fromInternalId.n_ids))
			
			# Checking consistency
			for intId in internalIds:
				if intId.nt_id not in self.acceptedNodeTypeIds:
					errmsg = f'Trying to use node {intId.n_payload_id} of unaccepted type in hyperedges for {joinInternalId.he_id}'
					self.logger.error(errmsg)
					raise TabLoaderIteratorException(errmsg)
			
			data = {
				"node_ids": list(map(lambda intId: intId.n_payload_id, internalIds))
			}
			if self.key_id is not None:
				hyperedgePayloadId = ''.join(self._fill_data(self.key_id, coldata))
				data["_id"] = hyperedgePayloadId
		
		return data, join_he_id, internalIds
