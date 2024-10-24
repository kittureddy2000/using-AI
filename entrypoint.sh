#!/bin/sh

# Exit immediately if a command exits with a non-zero status nad 
set -e

# Check the environment and set DB host accordingly
# if [ "$ENVIRONMENT" = "production" ]; then echo "Running in production environment"
    # Collect static files (for Google Cloud Storage or other static file service)
echo "Collecting static files..."
python manage.py collectstatic --noinput



DB_HOST="${DB_HOST:-db}"

# Wait for PostgreSQL to be ready
if [ "$ENVIRONMENT" != "production" ]; then

  echo "Waiting for PostgreSQL at $DB_HOST:5432..."
  while ! nc -z $DB_HOST 5432; do
    sleep 1
  done
  echo "PostgreSQL is up - continuing..."
fi

# Run database migrations
echo "python manage.py Before Running Migrations"
python manage.py makemigrations
echo "python manage.py Before Running migrate"
python manage.py migrate
echo "python manage.py migrate - Complete..."

# Start the Gunicorn server
gunicorn --bind 0.0.0.0:8080 samaanaiapps.wsgi:application

echo "gunicorn started"