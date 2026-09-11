#!/bin/bash
# Linux/Mac Script to Setup and Run Backend

echo ""
echo "========================================"
echo "Movie Trailer Sentiment Analysis Backend"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Download NLTK data
echo ""
echo "Setting up NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('vader_lexicon', quiet=True)"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p logs data models

# Display next steps
echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Add firebase-config.json to project root"
echo "3. Place finalized_movie_info.xlsx in data/ folder"
echo "4. Run: python scripts/clean_dataset.py"
echo "5. Run: python app.py"
echo ""
