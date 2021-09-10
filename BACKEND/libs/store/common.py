#!/usr/bin/env python3

import sqlite3
import json
try:
	# Trying to load a newer version
	import pysqlite3
	if pysqlite3.sqlite_version_info > sqlite3.sqlite_version_info:
		del sqlite3
		import pysqlite3 as sqlite3
except:
	pass

import json
import logging
import os
import os.path
from typing import Any, List, Mapping, NamedTuple, NewType, Tuple, Optional , Union
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


InternalHypergraphId = NewType('InternalHypergraphId', int)
InternalNodeTypeId = NewType('InternalNodeTypeId', int)
InternalEdgeTypeId = NewType('InternalEdgeTypeId', int)
InternalHyperedgeTypeId = NewType('InternalHyperedgeTypeId', int)
NodeTypeName = NewType('NodeTypeName', str)
EdgeTypeName = NewType('EdgeTypeName', str)
HyperedgeTypeName = NewType('HyperedgeTypeName', str)
SchemaId = NewType('SchemaId', str)

HypergraphPayloadId = NewType('HypergraphPayloadId', str)

InternalNodeId = NewType('InternalNodeId', int)
NodePayloadId = NewType('NodePayloadId', str)
NodePayloadName = NewType('NodePayloadName', str)

InternalEdgeId = NewType('InternalEdgeId', int)
EdgePayloadId = NewType('EdgePayloadId', str)

InternalHyperedgeId = NewType('InternalHyperedgeId', int)
HyperedgePayloadId = NewType('HyperedgePayloadId', str)

EpochSeconds = NewType('EpochSeconds', int)

class NodeType(NamedTuple):
	"""
	nt_id: The unique internal id of the node type
	name: The unique name of the node type
	"""
	nt_id: InternalNodeTypeId
	name: NodeTypeName
	schema_id: SchemaId
	description: Optional[str] = None
	number: Optional[int] = 0
	payload: Optional[Any] = None

class EdgeType(NamedTuple):
	"""
	et_id: The unique internal id of the edge type
	name: The unique name of the edge type
	"""
	et_id: InternalEdgeTypeId
	name: EdgeTypeName
	schema_id: SchemaId
	weight_name: Optional[str] = None
	weight_desc: Optional[str] = None
	description: Optional[str] = None
	number: Optional[int] = 0
	payload: Optional[Any] = None
	from_type: Optional[NodeType] = None
	to_type: Optional[NodeType] = None

class HyperedgeType(NamedTuple):
	"""
	het_id: The unique internal id of the hyperedge type
	name: The unique name of the hyperedge type
	"""
	het_id: InternalHyperedgeTypeId
	name: HyperedgeTypeName
	schema_id: SchemaId
	weight_name: Optional[str] = None
	weight_desc: Optional[str] = None
	description: Optional[str] = None
	number: Optional[int] = 0
	payload: Optional[Any] = None
	node_types: Optional[List[NodeType]] = None

class HypergraphId(NamedTuple):
	"""
	"""
	h_id: InternalHypergraphId
	stored_at: EpochSeconds
	updated_at: EpochSeconds
	h_payload_id: HypergraphPayloadId

class NodeId(NamedTuple):
	"""
	"""
	n_id: InternalNodeId
	nt_id: InternalNodeTypeId
	n_payload_id: NodePayloadId
	n_payload_name: NodePayloadName
	payload: Optional[Any] = None

class EdgeId(NamedTuple):
	"""
	"""
	e_id: InternalEdgeId
	et_id: InternalEdgeTypeId
	e_payload_id: EdgePayloadId
	from_id: InternalNodeId
	to_id: InternalNodeId
	from_payload_id: Optional[NodePayloadId] = None
	to_payload_id: Optional[NodePayloadId] = None
	weight: Optional[float] = None
	payload: Optional[Any] = None

class HyperedgeId(NamedTuple):
	"""
	"""
	he_id: InternalHyperedgeId
	het_id: InternalHyperedgeTypeId
	he_payload_id: HyperedgePayloadId
	n_ids: List[InternalNodeId]
	n_payload_ids: Optional[List[NodePayloadId]] = None
	weight: Optional[float] = None
	payload: Optional[Any] = None

class HyperedgeMemberDef(NamedTuple):
	"""
	"""
	className: Union[NodeTypeName, EdgeTypeName, HyperedgeTypeName]
	keyType: Union[NodeType, EdgeType, HyperedgeType]
	key: List[str]

class UnpackDef(NamedTuple):
	"""
	"""
	colNumber: int
	splitExp: List[str]
