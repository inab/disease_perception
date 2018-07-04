# Install instructions of Disease PERCEPTION REST API

The source code of this API is written for Python 3.5 or later. It depends on standard libreries, plus the ones declared in [requirements.txt](requirements.txt).

* In order to install the dependencies you need `pip` and `venv` Python modules.
	- `pip` is available in many Linux distributions (Ubuntu package `python-pip`, CentOS EPEL package `python-pip`), and also as [pip](https://pip.pypa.io/en/stable/) Python package.
	- `venv` is also available in many Linux distributions (Ubuntu package `python3-venv`). In some of these distributions `venv` is integrated into the Python 3.5 (or later) installation.

* The creation of a virtual environment and installation of the dependencies in that environment is done running:

```bash
python3 -m venv .pyRESTenv
source .pyRESTenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -c constraints.txt
# Next commands are to assure a static swagger ui interface is in place
if [ ! -d .pyRESTenv/lib/python3.5/site-packages/flask_restplus/static ] ; then
	wget --content-disposition https://github.com/swagger-api/swagger-ui/archive/v3.14.2.tar.gz
	tar xf swagger-ui-3.14.2.tar.gz swagger-ui-3.14.2/dist
	mv swagger-ui-3.14.2/dist .pyRESTenv/lib/python3*/site-packages/flask_restplus/static
	rm -r swagger-ui-3.14.2*
fi
```

