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
SchemaId = NewType('SchemaId', str)

HypergraphPayloadId = NewType('HypergraphPayloadId', str)

InternalNodeId = NewType('InternalNodeId', int)
NodePayloadId = NewType('NodePayloadId', str)

InternalEdgeId = NewType('InternalEdgeId', int)
EdgePayloadId = NewType('EdgePayloadId', str)

InternalHyperedgeId = NewType('InternalHyperedgeId', int)
HyperedgePayloadId = NewType('HyperedgePayloadId', str)

class NodeType(NamedTuple):
	"""
	nt_id: The unique internal id of the node type
	name: The unique name of the node type
	"""
	nt_id: InternalNodeTypeId
	name: str
	schema_id: SchemaId

class EdgeType(NamedTuple):
	"""
	et_id: The unique internal id of the edge type
	name: The unique name of the edge type
	"""
	et_id: InternalEdgeTypeId
	name: str
	schema_id: SchemaId
	weight_name: Optional[str]

class HyperedgeType(NamedTuple):
	"""
	het_id: The unique internal id of the hyperedge type
	name: The unique name of the hyperedge type
	"""
	het_id: InternalHyperedgeTypeId
	name: str
	schema_id: SchemaId
	weight_name: Optional[str]

class HypergraphId(NamedTuple):
	"""
	"""
	h_id: InternalHypergraphId
	stored_at: int
	updated_at: int
	h_payload_id: HypergraphPayloadId

class NodeId(NamedTuple):
	"""
	"""
	n_id: InternalNodeId
	nt_id: InternalNodeTypeId
	n_payload_id: NodePayloadId
	n_payload_name: str
	payload: Optional[Any] = None

class EdgeId(NamedTuple):
	"""
	"""
	e_id: InternalEdgeId
	et_id: InternalEdgeTypeId
	e_payload_id: EdgePayloadId
	from_id: InternalNodeId
	to_id: InternalNodeId

class HyperedgeId(NamedTuple):
	"""
	"""
	he_id: InternalHyperedgeId
	het_id: InternalHyperedgeTypeId
	he_payload_id: HyperedgePayloadId
	n_ids: List[InternalNodeId]

class HyperedgeMemberDef(NamedTuple):
	"""
	"""
	className: str
	keyType: Union[NodeType, EdgeType, HyperedgeType]
	key: List[str]

class UnpackDef(NamedTuple):
	"""
	"""
	colNumber: int
	splitExp: List[str]
