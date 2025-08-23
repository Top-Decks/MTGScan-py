#!/bin/sh
source .env
poetry run celery -A app.celery worker -P eventlet --loglevel=info &
poetry run gunicorn -w 8 -k eventlet --timeout 120 -b 0.0.0.0:5002 app:app