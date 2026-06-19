# Use the official Python slim image for a smaller footprint
FROM python:3.12-slim

# Set environment variables for Python optimization
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# PYTHONUNBUFFERED: Ensures stdout and stderr are streamed instantly without buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user for security best practices
RUN adduser --disabled-password --gecos '' appuser

# Set the working directory inside the container
WORKDIR /app

# Install necessary system dependencies (gcc is often needed for compiling ML packages)
# We clean up the apt cache immediately (`rm -rf`) to keep the image layer as small as possible
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY requirements.txt first to leverage Docker's layer caching.
# This means if you change your code but not your requirements, Docker won't redownload all packages.
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir keeps the image small by preventing pip from caching downloaded package archives
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure runtime directories exist and assign ownership to the non-root user
RUN mkdir -p /app/uploads /app/logs /app/faiss_index && \
    chown -R appuser:appuser /app

# Switch to the non-root user for all subsequent commands (Security Best Practice)
USER appuser

# Expose the port that FastAPI will run on
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
