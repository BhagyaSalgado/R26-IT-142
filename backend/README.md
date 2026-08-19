# Movie Trailer Comment Sentiment Analysis - Backend

Complete **Phase 3** backend with Firebase integration, BERT fine-tuning, and fallback models.

## 📋 Project Structure

```
movie-trailer-analyzer-backend/
├── config/                    # Configuration
│   ├── settings.py           # Main settings
│   └── constants.py          # Constants and keywords
├── models/                   # ML Models
│   ├── sentiment_model.py    # BERT with fallback chain
│   ├── preprocessor.py       # Text preprocessing
│   ├── topic_extractor.py    # Topic identification
│   └── language_detector.py  # Language detection
├── services/                 # Business Logic
│   ├── sentiment_service.py  # Main sentiment service
│   └── firebase_service.py   # Firebase database
├── api/                      # API Routes
│   └── routes.py            # REST endpoints
├── utils/                    # Utilities
│   ├── logger.py            # Logging setup
│   └── helpers.py           # Helper functions
├── scripts/                  # Utility Scripts
│   └── clean_dataset.py     # Data cleaning
├── tests/                    # Tests
│   └── test_sentiment_service.py
├── app.py                    # Main Flask app
├── requirements.txt          # Dependencies
├── .env                      # Configuration (update this!)
└── .env.example             # Example configuration
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Or run setup script
python setup.py
```

### 2. Configure Environment

```bash
# Copy and update .env
cp .env.example .env
```

Update `.env` with:
- `FIREBASE_CREDENTIALS`: Path to firebase-config.json
- `FIREBASE_DATABASE_URL`: Your Firebase Realtime Database URL
- `YOUTUBE_API_KEY`: Your YouTube API key (optional)
- `SECRET_KEY`: Change to a secure random string

### 3. Add Firebase Credentials

Download your Firebase credentials JSON from Firebase Console and save as `firebase-config.json` in project root.

### 4. Prepare Dataset

```bash
# Put your Excel file in project root or update path in clean_dataset.py
# Expected: finalized_movie_info.xlsx with columns: [comment, sentiment]

python scripts/clean_dataset.py
```

### 5. Run Backend

```bash
python app.py
```

Server runs on `http://localhost:5000`

## 📊 API Endpoints

### Health Check
```
GET /api/sentiment/health
```

### Analyze Comments (Main)
```
POST /api/sentiment/analyze
Content-Type: application/json

{
  "comments": ["comment1", "comment2", ...],
  "trailer_id": "trailer_123"
}

Response:
{
  "success": true,
  "data": {
    "sentiment": {"positive": 60, "neutral": 30, "negative": 10},
    "deeperEmotions": {"anticipation": 55, "excitement": 48, "disappointment": 6},
    "commentTopics": [
      {"topic": "Actors", "mentions": 25}
    ],
    "regionalInterest": [
      {"region": "United States", "value": 45.5}
    ],
    "totalComments": 100,
    "modelMetrics": {...}
  }
}
```

### Analyze Single Comment
```
POST /api/sentiment/analyze-single
Content-Type: application/json

{
  "comment": "This movie looks amazing!"
}
```

### Get Model Info
```
GET /api/sentiment/model-info
```

### System Status
```
GET /api/sentiment/status
```

## 🤖 Models (Fallback Chain)

1. **BERT** (Primary) - Most accurate, slower
2. **DistilBERT** - Faster, good accuracy
3. **VADER** - Rule-based, very fast
4. **TextBlob** - Lightweight fallback

Models auto-select based on availability.

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | development | Environment mode |
| `PRIMARY_MODEL` | bert-base-uncased | Primary model |
| `USE_FALLBACK` | true | Enable fallback models |
| `BATCH_SIZE` | 32 | Batch size for processing |
| `TRAINING_EPOCHS` | 3 | BERT fine-tuning epochs |

## 📝 Data Format

### Input (Excel File)
```
| Comment | Sentiment |
|---------|-----------|
| Great movie! | positive |
| Not good | negative |
| It's okay | neutral |
```

### Expected Sentiment Labels
- `positive` / `pos` → `POSITIVE`
- `negative` / `neg` → `NEGATIVE`
- `neutral` → `NEUTRAL`

Data cleaning script handles:
- Case normalization
- Whitespace trimming
- Typo correction
- Duplicate removal
- Empty row removal

## 🧪 Testing

```bash
# Test sentiment service
python tests/test_sentiment_service.py

# Clean and prepare dataset
python scripts/clean_dataset.py
```

## 📦 Dependencies

**Core:**
- Flask 2.3.2 - Web framework
- transformers 4.29.2 - BERT models
- torch 2.0.1 - Deep learning

**NLP:**
- nltk 3.8.1 - Text processing
- scikit-learn 1.3.0 - ML utilities

**Database:**
- firebase-admin 6.1.0 - Firebase integration

**Data:**
- pandas 2.0.2 - Data manipulation
- openpyxl 3.10.0 - Excel reading

## ⚠️ Important Notes

1. **Firebase Setup Required**
   - Create Firebase Realtime Database
   - Download credentials JSON
   - Set DATABASE_URL in .env

2. **First Run**
   - BERT models download automatically (~400MB)
   - Takes time on first prediction
   - Subsequent calls are faster

3. **Production Deployment**
   - Change SECRET_KEY in .env
   - Use environment-specific .env files
   - Deploy on proper server (not Flask dev)
   - Consider using Gunicorn + Nginx

## 🐛 Troubleshooting

**Model loading fails?**
```
Falls back automatically. Check logs in ./logs/
```

**Firebase connection error?**
```
Verify firebase-config.json exists
Check FIREBASE_DATABASE_URL in .env
```

**Out of memory?**
```
Reduce BATCH_SIZE in .env
Use DistilBERT instead of BERT
```

## 📊 Sentiment Analysis Features

### Basic Sentiment
- Positive / Negative / Neutral classification
- Confidence scores

### Deeper Emotions
- Anticipation
- Excitement
- Disappointment

### Topic Extraction
- Actors, Music, Visual Effects, etc.
- Mention counts

### Regional Interest
- Language detection
- Regional distribution

## 🔄 Integration with Frontend

Frontend sends comments to:
```
POST http://localhost:5000/api/sentiment/analyze
```

Response automatically stored in Firebase and returned to frontend.

## 📚 Documentation Files

- [SENTIMENT_ANALYSIS_PART.md](../SENTIMENT_ANALYSIS_PART.md) - Overview
- [BACKEND_IMPLEMENTATION.md](../BACKEND_IMPLEMENTATION.md) - Implementation guide
- [TESTING_GUIDE.md](../TESTING_GUIDE.md) - Testing

---

**🎉 Backend ready for Phase 3!**
