#!/bin/sh
set -e

echo "Starting production backend..."

if [ "$DATABASE" = "postgres" ]; then
    echo "Waiting for PostgreSQL..."

    while ! nc -z "$SQL_HOST" "$SQL_PORT"; do
        sleep 1
    done

    echo "PostgreSQL is ready."
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec "$@"
