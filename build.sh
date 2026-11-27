#!/usr/bin/env bash
# Executado pelo Render a cada deploy.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
