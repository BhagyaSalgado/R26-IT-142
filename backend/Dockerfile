"""
Docker Configuration - Deploy backend in container
"""

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt stopwords wordnet vader_lexicon

# Copy application
COPY . .

# Create directories
RUN mkdir -p logs data models

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
