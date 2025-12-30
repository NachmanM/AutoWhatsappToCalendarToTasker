# Start with a lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# --- INSTALL NODE.JS & GEMINI CLI ---
# We need Node.js because 'gemini-cli' is a Node tool
RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @google/gemini-cli \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- INSTALL PYTHON DEPENDENCIES ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script
COPY . .

# Create the images directory
RUN mkdir -p waha_images

# Run the script
CMD ["python", "main.py"]
