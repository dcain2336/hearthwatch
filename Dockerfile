# Hearthwatch container image.
# Slim Python base keeps the image small; OpenCV needs the system
# video libraries below (the pip wheel links against them).
FROM python:3.12-slim

# Install the shared libraries OpenCV links against at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Work inside /app for the rest of the build.
WORKDIR /app

# Install pinned Python dependencies first (cached layer).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source.
COPY src/ ./src/

# The demo server listens on port 8772.
EXPOSE 8772

# Start the demo server on container launch.
CMD ["python3", "src/app.py", "8772"]
