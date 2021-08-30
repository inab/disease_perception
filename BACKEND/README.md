# Disease PERCEPTION REST API

* Before running the Disease PERCEPTION REST API, please follow the instructions in [INSTALL.md](INSTALL.md), and populate the database using the instructions available in [../DB/INSTALL.md](../DB/INSTALL.md).


* The API can be run at http://localhost:5000 in debug mode using the next command line:

```bash
source .pyRESTenv/bin/activate
python como_network.py
```

  If you open http://localhost:5000/api , you can test the API using [Swagger UI](https://swagger.io/swagger-ui/). The API definition is reachable at http://localhost:5000/api/swagger.json 

* This directory holds a FastCGI executable, so it can be integrated into an Apache instance. Please follow the instructions of API integration into Apache in [INSTALL.md](INSTALL.md). 
