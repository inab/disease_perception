#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

import sys, os

import libs.app

from flup.server.fcgi import WSGIServer

import yaml
# We have preference for the C based loader and dumper, but the code
# should fallback to default implementations when C ones are not present
try:
	from yaml import CLoader as YAMLLoader, CDumper as YAMLDumper
except ImportError:
	from yaml import Loader as YAMLLoader, Dumper as YAMLDumper

# Creating the object holding the state of the API
if hasattr(sys, 'frozen'):
	basis = sys.executable
else:
	basis = sys.argv[0]

api_root = os.path.split(basis)[0]

# Setup tweaks
config_file = basis + '.yaml'
if os.path.exists(config_file):
	with open(config_file,"r",encoding="utf-8") as cf:
		local_config = yaml.load(cf,Loader=YAMLLoader)
else:
	local_config = {}

# Connection to the database, setting up the default path
dbpath = local_config.setdefault("db", os.path.join('DB','net_comorbidity.db'))
if not os.path.isabs(dbpath):
	local_config['db'] = os.path.normpath(os.path.join(api_root, dbpath))

app = libs.app.init_comorbidities_app(local_config)

if __name__ == '__main__':
	if len(sys.argv) > 1:
		host = local_config.get('host',"0.0.0.0")
		port = local_config.get('port',5000)
		debug = sys.argv[1] != 'standalone'
		if debug:
			# Let's suppose it's a numerical port
			try:
				port = int(sys.argv[1])
			except ValueError:
				pass
			
			# Debug mode should not be tied to any interface
			host = "127.0.0.1"
		
		app.run(debug=debug, port=port, host=host, threaded=False, processes=1)
	else:
		from flup.server.fcgi import WSGIServer

		WSGIServer(app).run()
