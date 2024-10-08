#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL is up - continuing..."

# Run database migrations
python manage.py migrate

echo "python manage.py migrate - Complete..."

# Start the Gunicorn server
gunicorn --bind 0.0.0.0:8080 samaanaiapps.wsgi:application

echo "gunicorn started"