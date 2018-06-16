from werkzeug.routing import BaseConverter

class ListConverter(BaseConverter):

	"""Matches one of the items provided.  Items can either be Python
	identifiers or strings::
	
		Rule('/<any(about, help, imprint, class, "foo,bar"):page_name>')
	
	:param map: the :class:`Map`.
	:param items: this function accepts the possible items as positional
		arguments.
	"""

	def __init__(self, map, subconverterName='string', sep=',', *subconverterParams):
		BaseConverter.__init__(self, map)
		self.sep = sep
		self.subconverterName = subconverterName
		self.subconverterParams = subconverterParams
		
	def to_python(self, value):
		# Lazy initialization of the subconverter instance
		if not hasattr(self,'subconverter'):
			self.subconverter = self.map.converters[self.subconverterName](self.map,*self.subconverterParams)
		
		results = [ self.subconverter.to_python(result) for result in value.split(self.sep) ]
		
		return results
	
	def to_url(self, values):
		return self.sep.join(BaseConverter.to_url(str(value))
			for value in values)
