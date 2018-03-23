# coding: utf-8
import os, json
import pandas as pd
import sqlite3


def main():
    project_folder = "./"
    data_folder = os.path.join(project_folder,'data')
    output_folder = os.path.join(project_folder,'out')
    sql_creates_fname = os.path.join(data_folder, 'sql_create_tables.json')
    db_path = os.path.join(output_folder,'net_comorbidity.db')

    table_names = ["disease_group", "disease", "patient_subgroup", "gene", "study", "drug",
                   "patient", "patient_drug_maps", "patient_gene_maps", "patient_graph",
                   "disease_digraph", "patient_subgroup_digraph", "patient_subgroup_drug_intersect",
                   "patient_subgroup_gene_intersect"]

    # Create a dict with dataframes for each table: {tab_name -> df_table}
    df_dict = dict()
    for tab_name in table_names:
        fname = os.path.join(data_folder, tab_name)
        fname += ".tsv"
        df = pd.read_csv(fname, sep='\t')
        df_dict[tab_name] = df.set_index('id')

    # Load dict from json: {tab_name -> SQL Create}
    with open(sql_creates_fname) as fh:
        tables_sql = json.load(fh)

    if os.path.isfile(db_path):
        os.remove(db_path)

    con_db = sqlite3.connect(db_path)
    cursor = con_db.cursor()

    print("Creating Tables")

    for tab_name in table_names:
        sql = tables_sql[tab_name]
        print("Creating table %s" % tab_name)
        cursor.execute(sql)
        print("Inserting data")
        df_dict[tab_name].to_sql(tab_name, con_db, if_exists='append')
        print("done")
        print("-------------")
        
        
    print("Tables Ready")        

    con_db.commit()
    con_db.close()


main()
