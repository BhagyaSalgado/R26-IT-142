@echo off
REM Windows Script to Setup and Run Backend

echo.
echo ========================================
echo Movie Trailer Sentiment Analysis Backend
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Download NLTK data
echo.
echo Setting up NLTK data...
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('vader_lexicon', quiet=True)"

REM Create necessary directories
echo.
echo Creating directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "models" mkdir models

REM Display next steps
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Update .env file with your configuration
echo 2. Add firebase-config.json to project root
echo 3. Place finalized_movie_info.xlsx in data/ folder
echo 4. Run: python scripts/clean_dataset.py
echo 5. Run: python app.py
echo.
pause
