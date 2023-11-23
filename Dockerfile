
# Use Python 3.10 image as the parent image
FROM python:3.10-slim

# Define environment variable
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Copy Google Cloud credentials into the container
#COPY using-ai-405105-5e2a1c2c69d8.json /app
#ENV GOOGLE_APPLICATION_CREDENTIALS=/app/using-ai-405105-5e2a1c2c69d8.json

# Start Cloud SQL Proxy
#COPY cloud-sql-proxy /app
#RUN chmod +x /app/cloud-sql-proxy
#RUN ./cloud-sql-proxy -instances=using-ai-405105:us-west1:mypostgres=tcp:5432 &

# Run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "samaanaiapps.wsgi:application"]
