#!/bin/bash

CWD=`pwd`

VIRTUALENV_PATH=${CWD}/venv
if [ ! -d "${VIRTUALENV_PATH}" ]
then
    if [ $1 ]
    then
        VARIANT=$1
    else
        VARIANT=mysql
    fi
    echo "Virtualenv not created. trying creating virtualenv for '${VARIANT}'..."
    REQUIREMENTS_FILE="./requirements/${VARIANT}.txt"
    if [ ! -e ${REQUIREMENTS_FILE} ]
    then
        echo "${REQUIREMENTS_FILE} does not exist"
        exit -1
    fi
    virtualenv venv || (echo "Virtualenv is not installed" && exit -1)
    . ${VIRTUALENV_PATH}/bin/activate
    pip install -r ${REQUIREMENTS_FILE} || (echo "Virtualenv creation unsuccessful" && exit -1)
    patch -p1 -d venv/lib/python2.7/site-packages < twisted.patch.diff
    deactivate
fi