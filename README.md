# Disease PERCEPTION 1

**PER**sonalized **C**omorbidity **E**x**P**lora**TION**

Latest public version: [![DOI](https://zenodo.org/badge/126212770.svg)](https://zenodo.org/badge/latestdoi/126212770)

<img src="docs/disease_perception_curves.svg" alt="Disease PERCEPTION logo" width="200" />

## How to deploy Disease PERCEPTION 1 using `docker compose`

Recently, this repository has received an uplift, in order to automatically generate its own containers and start the service by its own.

Once you have properly installed both `docker` and `docker compose` plugin following standard procedures, you only have to run it:

```bash
docker compose pull
docker compose up --no-build -d
```

Several setup parameters can be changed at [.env](.env) file.

There is a one shot job which automatically generates the comorbidities database.


## API integration into Apache

This API can be integrated into an Apache instance. The instance must have the module `mod_proxy_uwsgi` installed
(package [libapache2-mod-proxy-uwsgi](https://packages.ubuntu.com/noble/libapache2-mod-proxy-uwsgi) in Ubuntu 24.04).

```bash
sudo apt-get install libapache2-mod-proxy-uwsgi
sudo a2enmod proxy_uwsgi
sudo systemctl restart apache2
```

```apache config
	<Location />
		ProxyPass "uwsgi://192.168.0.186:5000/"
		ProxyPassReverse "uwsgi://192.168.0.186:5000/"
		ProxyAddHeaders On
		ProxyPreserveHost On
	</Location>
```
