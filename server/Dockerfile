# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
RUN mkdir /app
WORKDIR /app

# Copy the requirements file into the container
# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Copy the rest of the server code into the container
COPY . /app

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the server
CMD ["python", "main.py"]