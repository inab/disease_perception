#!/usr/bin/env python3

import sqlite3
try:
	# Trying to load a newer version
	import pysqlite3
	if pysqlite3.sqlite_version_info > sqlite3.sqlite_version_info:
		del sqlite3
		import pysqlite3 as sqlite3
except:
	pass

import logging
import sys

# We have preference for the C based loader and dumper, but the code
# should fallback to default implementations when C ones are not present
import yaml
try:
	from yaml import CLoader as YAMLLoader, CDumper as YAMLDumper
except ImportError:
	from yaml import Loader as YAMLLoader, Dumper as YAMLDumper

from libs.store.hypergraphs_store import *

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