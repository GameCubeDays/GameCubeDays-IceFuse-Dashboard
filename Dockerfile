FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Copy the entire project
COPY . .

# Install Python dependencies
# First, upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install the package in development mode with dependencies
# This will work with either pyproject.toml or setup.py
RUN pip install --no-cache-dir -e .

# Alternative: If you prefer to just install from requirements.txt without package installation:
# RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the main script
CMD ["python", "main.py"]
