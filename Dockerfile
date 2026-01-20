# Use the official Python image as a parent image
FROM python:3.10-slim

# Set environment variables for Flask
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Set the working directory in the container
WORKDIR /app

# Copy the rest of your application code into the container
COPY . /app/

# Upgrade pip within the virtual environment
# Install any needed packages specified in requirements.txt
RUN pip cache purge && pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libcairo2-dev \
    libatlas-base-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Expose the port the application runs on
EXPOSE 5000

# Start Gunicorn with your Flask app
CMD ["gunicorn", "--workers=4", "--threads=1", "--timeout=360", "--bind=0.0.0.0:5000", "main:app"]
