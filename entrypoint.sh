#!/bin/sh
# Runs on every container start: apply migrations, then serve.
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn on :8000..."
exec gunicorn devlaunch_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
