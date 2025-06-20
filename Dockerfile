# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port that Gunicorn will run on
EXPOSE 8000

ENV FLASK_ENV=production

# Command to run the application using Gunicorn
# -w 4: Sets 4 worker processes (adjust based on your server's CPU cores, typically 2*CPU_CORES + 1).
# -b 0.0.0.0:8000: Binds Gunicorn to all network interfaces on port 8000.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]