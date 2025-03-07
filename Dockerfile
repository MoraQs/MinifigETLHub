# Use official Python image
FROM python:3.9

# Set working directory inside the container
WORKDIR /app/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    make \
    curl \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    libaio1 \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*  # Clean up apt-get cache to reduce image size

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts into the container
COPY scripts /app/scripts/

# Command to run your script (*.py includes all the Python scripts in the scripts folder)
CMD ["sh", "-c", "for script in /app/scripts/*.py; do python $script; done && tail -f /dev/null"]