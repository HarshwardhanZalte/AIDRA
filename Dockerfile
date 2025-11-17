# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the backend requirements file first
COPY backend/requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend folder into the container
COPY backend/ .

# Expose the port Cloud Run will use
EXPOSE 8080

# Command to run your app
# We use 0.0.0.0 to accept connections and $PORT (which 8080 is the default)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]