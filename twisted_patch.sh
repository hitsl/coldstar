#!/bin/sh

patch -p1 -d venv/lib/python2.7/site-packages < twisted.patch.diff