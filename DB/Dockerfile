FROM	alpine:3.21 AS build

WORKDIR	/usr/src/app
RUN	apk add --no-cache python3-dev py3-pip build-base

COPY	requirements.txt /usr/src/app

RUN	python3 -m venv /usr/src/app/.py3env && \
	source /usr/src/app/.py3env/bin/activate && \
	pip install --no-cache-dir --upgrade pip wheel && \
	pip install --no-cache-dir -r requirements.txt

FROM alpine:3.21 AS deploy

RUN apk add --no-cache python3 libgomp

COPY --from=build /usr/src/app /usr/src/app
COPY create_db.py /usr/src/app
