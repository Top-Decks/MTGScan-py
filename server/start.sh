#!/bin/sh
poetry run celery -A app.celery worker -P eventlet --loglevel=info &
poetry run python app.py