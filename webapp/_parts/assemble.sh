#!/bin/sh
set -e
mkdir -p webapp/static
# App.py from base64 parts A0-A6
cat webapp/_parts/A0 webapp/_parts/A1 webapp/_parts/A2 webapp/_parts/A3 webapp/_parts/A4 webapp/_parts/A5 webapp/_parts/A6 | base64 -d > webapp/app.py
# index.html from base64 parts H0-H5
cat webapp/_parts/H0 webapp/_parts/H1 webapp/_parts/H2 webapp/_parts/H3 webapp/_parts/H4 webapp/_parts/H5 | base64 -d > webapp/static/index.html
echo "assembled webapp v2 (A0-A6 + H0-H5)"
ls -la webapp/app.py webapp/static/index.html
