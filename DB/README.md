# Disease PERCEPTION database population

* Before running the comorbidities database population program, please follow the instructions in [INSTALL.md](INSTALL.md).

* The SQLite3 database is populated with all the comorbidities tables using the next command line:

```bash
source .pyDBenv/bin/activate
python create_db.py
deactivate
```

* The database file is called `net_comorbidity.db`, and it is available in the `../REST/DB` subdirectory.
