# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install ODBC driver dependencies and FFmpeg
RUN apt-get update && \
    apt-get install -y \
        curl \
        gnupg \
        apt-transport-https \
        unixodbc \
        unixodbc-dev \
        ffmpeg

# Install the Microsoft ODBC driver for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17
    

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run transcribe.py when the container launches
CMD ["python", "transcribe.py"]
