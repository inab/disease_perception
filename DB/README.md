# Disease PERCEPTION 1 database population

* Before running the comorbidities database population program, please follow the instructions in [INSTALL.md](INSTALL.md).

* The SQLite3 database is populated with all the comorbidities tables using the next command line:

  ```bash
  source .pyDBenv/bin/activate
  python create_db.py
  deactivate
  ```

  The database file is called `net_comorbidity.db`, and it is available in the `../REST/DB` subdirectory.

* The program is now parametrised:

  - The first parameter tells the source dataset directory.
    By default, it is at [data](data),
    and a file called [sql_create_tables.json](data/sql_create_tables.json)
    is expected. The file describes both the tables and the location
    of the files to feed those tables.
  
  - The second parameter is related to the SQLite3 database where all the
    co-morbidity data is being loaded. It can be either the directory where
    the `net_comorbidity.db` file is going to be deposited
    (by default, at `../REST/DB`), or the explicit file
    (by default, `../REST/DB/net_comorbidity.db`).
