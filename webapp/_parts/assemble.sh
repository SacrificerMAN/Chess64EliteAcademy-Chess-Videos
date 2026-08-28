#!/bin/sh
set -e
mkdir -p webapp/static
cat webapp/_parts/app.0 webapp/_parts/app.1 webapp/_parts/app.2 webapp/_parts/app.3 > webapp/app.py
cat webapp/_parts/html.0 webapp/_parts/html.1 webapp/_parts/html.2 webapp/_parts/html.3 > webapp/static/index.html
echo "assembled webapp v2"
