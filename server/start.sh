#!/bin/sh
poetry run celery -A app.celery worker -P eventlet --loglevel=info &
poetry run gunicorn -w 8 -k gthread -b 0.0.0.0:5002 app:app