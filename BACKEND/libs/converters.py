#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

from werkzeug.routing import BaseConverter

class ListConverter(BaseConverter):

	"""Matches one of the items provided.  Items can either be Python
	identifiers or strings::
	
		Rule('/<list(int, sep=","):page_name>')
	
	:param map: the :class:`Map`.
	:param items: this function accepts the possible items as positional
		arguments.
	"""

	def __init__(self, mapping, subtype=None, sep=',', *subconverterParams, **subconverterKwParams):
		super().__init__(mapping)
		self.sep = sep
		self.subconverterName = subtype
		self.subconverterParams = subconverterParams
		self.subconverterKwParams = subconverterKwParams
		
	def _allocate_subconverter(self):
		if not hasattr(self,'subconverter'):
			self.subconverter = self.map.converters[self.subconverterName](self.map, *self.subconverterParams, **self.subconverterKwParams)
	
	def to_python(self, value):
		results = str(value).split(self.sep)
		
		if self.subconverterName is not None:
			# Lazy initialization of the subconverter instance
			self._allocate_subconverter()
			results = [ self.subconverter.to_python(r) for r in results ]
		
		return results
	
	def to_url(self, value):
		retval_it = None
		if self.subconverterName is not None:
			self._allocate_subconverter()
			retval_it = map(lambda v: self.subconverter.to_url(v), value)
		else:
			retval_it = map(lambda v: super(PathConverter, self).to_url(str(v)), value)
		
		return self.sep.join(retval_it)

import urllib.parse
from werkzeug.routing import PathConverter

class SplitPathConverter(PathConverter):

	"""Matches one of the items provided.  Items can either be Python
	identifiers or strings::
	
		Rule('/<any(about, help, imprint, class, "foo,bar"):page_name>')
	
	:param map: the :class:`Map`.
	:param items: this function accepts the possible items as positional
		arguments.
	"""
	
	def __init__(self, mapping, decode:bool=False, sub=None, *subconverterParams, **subconverterKwParams):
		super().__init__(mapping)
		self.doUrlDecode = decode
		self.subconverterName = sub
		self.subconverterParams = subconverterParams
		self.subconverterKwParams = subconverterKwParams
	
	def _allocate_subconverter(self):
		if not hasattr(self,'subconverter'):
			self.subconverter = self.map.converters[self.subconverterName](self.map, *self.subconverterParams, **self.subconverterKwParams)
	
	def to_python(self, value):
		# Lazy initialization of the subconverter instance
		retval = value.split('/')
		if self.doUrlDecode:
			retval = [ urllib.parse.unquote(tok)  for tok in retval ]
		
		if self.subconverterName is not None:
			self._allocate_subconverter()
			retval = [ self.subconverter.to_python(r) for r in retval ]
		
		return retval
	
	def to_url(self, value):
		retval_it = None
		if self.subconverterName is not None:
			self._allocate_subconverter()
			retval_it = map(lambda v: self.subconverter.to_url(v), value)
		else:
			retval_it = map(lambda v: super(PathConverter, self).to_url(str(v)), value)
		
		if self.doUrlDecode:
			retval_it = map(lambda p: urllib.parse.quote(p), retval_it)
		
		return '/'.join(retval_it)
