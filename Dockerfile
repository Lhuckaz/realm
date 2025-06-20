# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port that Gunicorn will run on
EXPOSE 8000

# Command to run the application using Gunicorn
# Gunicorn is a production-ready WSGI HTTP Server.
# We're binding to 0.0.0.0 to make it accessible from outside the container.
# All necessary URLs and the API key will be passed via environment variables during 'docker run'.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]