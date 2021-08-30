#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8
import sys, os, json
import pandas as pd
import sqlite3

def main(project_folder="./"):
	data_folder = os.path.join(project_folder,'data')
	output_folder = os.path.join(project_folder,'..','REST','DB')
	
	os.makedirs(output_folder,exist_ok=True)
	
	sql_creates_fname = os.path.join(data_folder, 'sql_create_tables.json')
	db_path = os.path.join(output_folder,'net_comorbidity.db')
	
	# Load list of dicts from json: [{tab_name, SQL Create,datafile}]
	with open(sql_creates_fname) as fh:
		table_decls = json.load(fh)
	
	con_db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES, check_same_thread = False)
	con_db.execute("""PRAGMA locking_mode = NORMAL""")
	con_db.execute("""PRAGMA journal_mode = WAL""")
	with con_db:
		cursor = con_db.cursor()
		cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
		numTablesRes = cursor.fetchone()
		
		# We have to drop all the tables with the same name as the new ones before starting
		if numTablesRes and numTablesRes[0] > 0:
			print("Dropping old tables")
			for table in reversed(table_decls):
				tab_name = table['table']
				print("* Drop table {0} (if exists)".format(tab_name))
				cursor.execute("DROP TABLE IF EXISTS {0};".format(tab_name))
				
		print("Creating tables")
		
		for table in table_decls:
			tab_name = table['table']
			print("* Creating table %s" % tab_name)
			
			sql_creation_arr = table['sql_ddl']
			cursor.execute("CREATE TABLE {0} ( {1} );".format(tab_name,", ".join(sql_creation_arr)))
			
			fname = os.path.join(data_folder,table['datafile'])
			print("\t- Reading file {0}".format(fname))
			idf = pd.read_csv(fname, sep='\t', chunksize=100000)
			#df_id = df.set_index('id')
			print("\t- Inserting data into {0}".format(tab_name))
			#df_id.to_sql(tab_name, con_db, if_exists='append')
			for chunk in idf:
				chunk.to_sql(tab_name, con_db, if_exists='append',index=False)
			
			indexes = table.get('indexes',[])
			for index in indexes:
				indexCommas = ', '.join(index)
				print("\t- Indexing column(s): {0}".format(indexCommas))
				index_ddl = "CREATE INDEX {0} ON {1} ({2});".format(tab_name+'_fk_'+'_'.join(index),tab_name,indexCommas)
				cursor.execute(index_ddl)
			
			print("\t- Done!")
	con_db.execute("""PRAGMA journal_mode = DELETE""")
	
	print("Tables Ready")        
	con_db.close()


if hasattr(sys, 'frozen'):
	basis = sys.executable
else:
	basis = sys.argv[0]

project_folder = os.path.split(basis)[0]

main(project_folder)
