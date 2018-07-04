#!/bin/bash

REALPATH="$(realpath "$0")"
BASEDIR="$(dirname "$REALPATH")"
case "$BASEDIR" in
	/*)
		true
		;;
	*)
		BASEDIR="${PWD}/$BASEDIR"
		;;
esac

PYBASEDIR="${BASEDIR}/.pyRESTenv"
# Is there a prepared Python environment??
if [ ! -d "$PYBASEDIR" ] ; then
	python3 -m venv "$PYBASEDIR"
	source "$PYBASEDIR"/bin/activate
	pip install --upgrade pip
	pip install -r "${BASEDIR}"/requirements.txt -c "${BASEDIR}"/constraints.txt
fi

if [ -d "$PYBASEDIR" ] ; then
	source "${PYBASEDIR}/bin/activate"
	exec python "${BASEDIR}/$(basename "$0")".py "$@"
else
	echo "UNCONFIGURED" 1>&2
	exit 1
fi
