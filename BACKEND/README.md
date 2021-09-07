# Disease PERCEPTION Backend and REST API

* Before running the Disease PERCEPTION Backend and REST API, please follow the instructions in [INSTALL.md](INSTALL.md), and populate the database using next command line:

  ```bash
  python offline_data_loader.py DB/net_comorbidity.db ../DATA/meta/manifest.json ../DATA/disease-perception/data-manifest.yaml
  ```

* The API can be run at http://localhost:5000 in standalone or debug mode using the next command lines:

  ```bash
  ./disease_perception.fcgi standalone
  ```

  ```bash
  ./disease_perception.fcgi debug
  ```

  If you open http://localhost:5000/api , you can test the API using [Swagger UI](https://swagger.io/swagger-ui/). The API definition is reachable at http://localhost:5000/api/swagger.json 

* This directory holds a FastCGI executable, so it can be integrated into an Apache instance. Please follow the instructions of API integration into Apache in [INSTALL.md](INSTALL.md). 
