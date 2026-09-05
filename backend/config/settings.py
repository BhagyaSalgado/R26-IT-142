import os
from dotenv import load_dotenv

load_dotenv()

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = FLASK_ENV == 'development'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# CORS Configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5174,http://localhost:3000').split(',')

# Model Configuration
PRIMARY_MODEL = os.getenv('PRIMARY_MODEL', 'distilbert-base-uncased-finetuned-sst-2-english')
SECONDARY_MODEL = os.getenv('SECONDARY_MODEL', 'cardiffnlp/twitter-roberta-base-sentiment-latest')
USE_FALLBACK = os.getenv('USE_FALLBACK', 'true').lower() == 'true'
MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', './.cache/models')

# Firebase Configuration
FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS', './firebase-config.json')
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL', '')

# YouTube Configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
YOUTUBE_MAX_COMMENTS = int(os.getenv('YOUTUBE_MAX_COMMENTS', '1000'))

# Training Configuration
TRAINING_EPOCHS = int(os.getenv('TRAINING_EPOCHS', '3'))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '32'))
LEARNING_RATE = float(os.getenv('LEARNING_RATE', '2e-5'))

# Data Configuration
DATA_DIR = os.getenv('DATA_DIR', './data')
CLEANED_DATA_PATH = os.path.join(DATA_DIR, 'cleaned_comments.csv')
MODEL_PATH = os.getenv('MODEL_PATH', './models/finetuned_bert')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', './logs/app.log')
