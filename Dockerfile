FROM	docker.io/library/node:24 AS build_frontend

WORKDIR	/app
COPY	FRONTEND /app
RUN	git config --global url."https://github".insteadOf ssh://git@github && \
	git config --global url."https://github.com/".insteadOf git@github.com: && \
	npm install --no-save npm node-gyp && \
	npm x -- npm install --no-save yarn && \
	npm x -- yarn install --frozen-lockfile && \
	npm x -- webpack -p --progress --colors


FROM	alpine:3.21 AS build_api

ARG	SWAGGER_UI_VER	5.21.0

WORKDIR	/usr/src/app
RUN	apk add --no-cache python3-dev py3-pip build-base

COPY	REST/requirements.txt ./LICENSE /usr/src/app

RUN	python3 -m venv /usr/src/app/.pyRESTenv && \
	source /usr/src/app/.pyRESTenv/bin/activate && \
	pip install --no-cache-dir --upgrade pip wheel && \
	pip install --no-cache-dir -r requirements.txt && \
	if [ ! -d .pyRESTenv/lib/python3.*/site-packages/flask_restx/static ] ; then \
		wget --content-disposition https://github.com/swagger-api/swagger-ui/archive/v${SWAGGER_UI_VER}.tar.gz ; \
		tar xf swagger-ui-${SWAGGER_UI_VER}.tar.gz swagger-ui-${SWAGGER_UI_VER}/dist ; \
		mv swagger-ui-${SWAGGER_UI_VER}/dist .pyRESTenv/lib/python3.*/site-packages/flask_restx/static ; \
		rm -r swagger-ui-${SWAGGER_UI_VER}* ; \
	fi


FROM	alpine:3.21 AS deploy

EXPOSE	5000
# RUN	apk add --no-cache uwsgi-python3 python3 libgomp
RUN	apk add --no-cache uwsgi-python3 python3

COPY	--from=build_api /usr/src/app /usr/src/app
COPY	--from=build_frontend /REST/static /usr/src/app/static
COPY	REST/uwsgi.ini REST/disease_perception.wsgi REST/disease_perception.py /usr/src/app
COPY	REST/libs /usr/src/app/libs

CMD	[ "uwsgi", "--ini", "/usr/src/app/uwsgi.ini" ]
