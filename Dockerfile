# Dockerfile

# Use the official Python image from Docker Hub
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set build-time variables
ARG ENVIRONMENT=production
ENV ENVIRONMENT=${ENVIRONMENT}

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app/

# Collect static files (if necessary)
#RUN python manage.py collectstatic --noinput

# Create a non-root user (optional but recommended)
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Expose port 8080
EXPOSE 8080

# Copy the entrypoint script
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
