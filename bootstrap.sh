#!/bin/bash

CWD=`pwd`

VIRTUALENV_PATH=$CWD/venv

if [ ! -d "$VIRTUALENV_PATH" ]
then
    [ ! -e config.yaml ] && cp config_dist.yaml config.yaml
    echo "Virtualenv not created. trying creating virtualenv..."
    virtualenv venv || (echo "Virtualenv is not installed" && exit -1)
    . $VIRTUALENV_PATH/bin/activate
    pip install -r ./requirements.txt || (echo "Virtualenv creation unsuccessful" && exit -1)
    patch -p1 -D /venv/lib/python2.7/site-packages < twisted.patch.diff
else
    echo "Activating virtualenv"
    . $VIRTUALENV_PATH/bin/activate
fi

# echo "Starting Coldstar..."

# PYTHONPATH=$CWD twistd -n coldstar

deactivate