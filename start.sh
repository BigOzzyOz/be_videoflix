#!/bin/sh
set -e

if [ "$ENV" = "production" ]; then
  echo "Running in PRODUCTION mode"
  python manage.py migrate
  python manage.py collectstatic --noinput
  exec gunicorn core.wsgi:application --bind 0.0.0.0:8002
else
  echo "Running in DEVELOPMENT mode"
  python manage.py migrate
  exec python manage.py runserver 0.0.0.0:8000
fi
