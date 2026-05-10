# Comment Sentiment Analysis - Your Responsibility

## 📋 ඔබගේ කොටස - Overview

**Component Name:** Comment Sentiment Analysis  
**Your Role:** Backend sentiment analysis model + API integration  
**Team Member:** De Silva T.R.R (IT22236296)  
**Project Code:** R26-IT-142

---

## 🎯 ඔබගේ වගකරණීයතා (Your Responsibilities)

### 1. **Data Collection Module** 📥
- **Task:** YouTube Data API සිට comments එක්කර ගත යුතුයි
- **Technologies:** Python, YouTube Data API
- **Output:** Comment dataset (text, timestamp, likes, user language)

### 2. **Text Preprocessing Module** 🧹
- Clean comments (URLs, special characters remove කරන්න)
- Tokenization (වචන වලට බෙදන්න)
- Stop-word removal
- Emoji handling
- Lemmatization (words normalize කරන්න)

**Input:** Raw comments  
**Output:** Cleaned, structured text data

### 3. **Language Detection Module** 🌐
- প্রতিটি comment ගේ language හඳුනාගනු  
- Geographic audience distribution identify කරන්න
- Examples: Spanish = Latin America, Hindi = India

### 4. **Sentiment Classification Module** 🤖
- **Model:** BERT (Bidirectional Encoder Representations from Transformers)
- **Framework:** PyTorch / TensorFlow
- **Library:** Hugging Face Transformers
- **Output Categories:** Positive, Neutral, Negative

**Key Algorithm:**
```
Raw Comment → BERT Embedding → Classification Layer → Sentiment Score
```

### 5. **Topic Extraction Module** 📌
- Comments එකින් frequently discussed topics හඳුනා ගන්න
- Topics: Actors, Storyline, Music, Visual Effects, Quality
- Frequency counting සිට top topics identify කරන්න

### 6. **Analytics & Visualization** 📊
- Sentiment distribution calculate කරන්න (%)
- Generate insights for marketing teams
- Create reports for decision-making

---

## 📦 Your Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.9+ | Backend implementation |
| **ML Framework** | PyTorch / TensorFlow | Model training & inference |
| **NLP Library** | Hugging Face Transformers | Pre-trained BERT model |
| **Text Processing** | NLTK / spaCy | Preprocessing & tokenization |
| **API** | YouTube Data API | Comment collection |
| **Database** | MongoDB | Store comments & results |
| **API Server** | Flask / FastAPI | REST endpoints for frontend |

---

## 🔄 System Flow - ඔබගේ කොටස

```
┌─────────────────────────────────────────────────────────────┐
│              COMMENT SENTIMENT ANALYSIS PIPELINE              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. [YouTube]                                                │
│       ↓ YouTube Data API                                     │
│  2. [Raw Comments] (text, timestamp, likes)                  │
│       ↓ Text Preprocessing                                   │
│  3. [Cleaned Comments] (normalized text)                     │
│       ↓ Language Detection                                   │
│  4. [Language Identified] (English, Spanish, Hindi, etc)    │
│       ↓ BERT Model                                           │
│  5. [Sentiment Scores] (positive%, neutral%, negative%)      │
│       ↓ Topic Extraction                                     │
│  6. [Topics Extracted] (Actors, Music, Storyline, etc)       │
│       ↓ Analytics Engine                                     │
│  7. [Sentiment Insights] (JSON)                              │
│       ↓ REST API                                             │
│  8. [Frontend Dashboard]                                     │
│       ├─ Pie Chart (Sentiment Distribution)                  │
│       ├─ Metric Cards (64% Positive)                         │
│       ├─ Region Analysis                                     │
│       └─ Topic Analysis                                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Frontend Integration - ඔබගේ Output භාවිතා

Frontend නේ **already implemented:**

### Sentiment Chart (Pie Chart)
```tsx
// File: src/components/Charts.tsx
sentiment: {
  positive: 64,    // Your model output
  neutral: 22,
  negative: 14
}
```

### Metric Cards
```tsx
// File: src/App.tsx - Card showing:
{
  title: 'Positive Sentiment',
  value: 64%,  // From your BERT model
  helper: 'BERT-based comment sentiment classification'
}
```

### Comment Topics (Backend)
```tsx
commentTopics: [
  { topic: 'Actors', mentions: 345 },      // Your extraction
  { topic: 'Music', mentions: 298 },
  { topic: 'Storyline', mentions: 267 }
]
```

---

## 🚀 Deliverables - ඔබ deliver කරන්න ඕනේ

### Phase 1: Model Development
- [ ] BERT model training code
- [ ] Sentiment classifier (positive/negative/neutral)
- [ ] Performance metrics (Accuracy, Precision, Recall, F1-score)

### Phase 2: Preprocessing Pipeline
- [ ] Text cleaning module
- [ ] Tokenization & lemmatization
- [ ] Emoji & special character handling
- [ ] Language detection

### Phase 3: Data Integration
- [ ] YouTube API integration
- [ ] Comment collection script
- [ ] MongoDB storage setup

### Phase 4: API Development
- [ ] Flask/FastAPI endpoints
- [ ] Sentiment analysis endpoint
- [ ] Topic extraction endpoint
- [ ] Analytics dashboard endpoint

### Phase 5: Documentation
- [ ] Model documentation
- [ ] API documentation (with examples)
- [ ] Deployment guide
- [ ] Performance benchmarks

---

## 📈 Key Metrics (ඔබ track කරන්න ඕනේ)

```
✓ Model Accuracy: Target 85%+
✓ Preprocessing quality: Clean ~95%+ comments
✓ API Response Time: < 500ms per request
✓ Topic extraction coverage: Capture 90%+ topics
✓ Language detection accuracy: 95%+
✓ Comment volume handled: 10,000+/batch
```

---

## 🤝 Team Structure

Your project team has multiple components:

```
AI-Powered Movie Trailer Analyzer
├── Comment Sentiment Analysis [YOU]
│   ├── BERT Model
│   ├── Text Preprocessing
│   └── Topic Extraction
├── Video Emotion Analysis [Team Member 2]
│   ├── Visual feature extraction
│   └── Scene intensity analysis
├── Audio Sentiment Analysis [Team Member 3]
│   ├── Audio feature extraction
│   └── Music emotion detection
└── Frontend Dashboard [Team Member 4]
    ├── React Components
    └── Visualizations
```

---

## 💬 Team Presentation Tips - ඔබ කියන්න ඕනේ

### Slide 1: Overview (30 seconds)
"Our Comment Sentiment Analysis component analyzes YouTube trailer comments using BERT-based NLP to classify sentiment into positive, neutral, and negative categories."

### Slide 2: Process (1 minute)
"Raw comments → Preprocessing → BERT Model → Sentiment scores (positive 64%, neutral 22%, negative 14%)"

### Slide 3: Key Features (45 seconds)
- Multi-language support (English, Spanish, Hindi, etc)
- Topic extraction (Actors, Music, Storyline)
- Real-time processing
- 85%+ model accuracy

### Slide 4: Integration (30 seconds)
"Our API provides JSON output that the Frontend team uses for dashboard visualization, showing real-time sentiment metrics and engagement predictions."

### Slide 5: Timeline (45 seconds)
Show Gantt chart phases from your proposal document:
- March-May: Literature & Data Collection
- May-June: Model Development
- June-July: Training & Testing
- July-August: Integration & Deployment

---

## 📂 Project Structure (Expected)

```
movie-trailer-analyzer-backend/
├── sentiment_analysis/
│   ├── models/
│   │   ├── bert_model.py          # BERT implementation
│   │   ├── preprocessor.py        # Text preprocessing
│   │   └── topic_extractor.py     # Topic extraction
│   ├── data/
│   │   ├── youtube_scraper.py     # API integration
│   │   └── dataset.csv            # Collected comments
│   ├── api/
│   │   ├── app.py                 # Flask/FastAPI server
│   │   └── routes.py              # API endpoints
│   └── tests/
│       ├── test_bert.py
│       └── test_preprocessing.py
├── requirements.txt
├── README.md
└── deployment/
    └── dockerfile
```

---

## 🔗 Frontend Connection

**API Endpoint Pattern:**
```
POST /api/analyze/sentiment
{
  "trailer_url": "https://youtube.com/...",
  "language": "en"
}

Response:
{
  "sentiment": {
    "positive": 64,
    "neutral": 22,
    "negative": 14
  },
  "topics": [
    { "topic": "Actors", "mentions": 345 },
    { "topic": "Music", "mentions": 298 }
  ],
  "confidence": 88,
  "model_metrics": {
    "accuracy": 0.87,
    "precision": 0.89,
    "recall": 0.85
  }
}
```

---

## 📚 Reference from Your Proposal

From **Section 4.2 of your Research Proposal:**

> "The Comment Sentiment Analysis component is to analyze audience reactions expressed through comments posted under movie trailers. This component extracts emotional sentiment, identifies discussion topics, and estimates the geographic distribution of audience reactions based on comment language."

**Your specific sub-modules:**
1. Comment Data Collection Module
2. Text Preprocessing Module
3. Language Detection Module
4. Sentiment Classification Module (BERT)
5. Topic Extraction Module
6. Sentiment and Topic Insight Output

---

## ⚠️ Important Notes

1. **API Rate Limiting:** YouTube API එකට limits තිබේ - handle කරන්න
2. **Model Size:** BERT model large - optimize කරන්න deployment එක්ට
3. **Privacy:** Public comments only - user data එක collect කරන්න එපා
4. **Testing:** Accuracy 85%+ achieve කරන්න බැලු ගන්න
5. **Documentation:** Code comments ලිවින්න team members clear උන්න

---

## 🎓 Final Checklist - Presentation වලට

- [ ] ඔබගේ component කුමන problem solve කරන්ද පැහැදිලි කරපු
- [ ] Architecture diagram පෙන්වපු
- [ ] Technologies & tools explain කරපු
- [ ] Team එකට කුමන data pass කරන්ද කිපු
- [ ] Timeline & deliverables present කරපු
- [ ] Demo / Mock results පෙන්වපු (frontend charts)
- [ ] Challenges & solutions discussed කරපු

---

## 📞 Integration Points

**Receive From:**
- Frontend Team: Dashboard component specs
- Video Analysis Team: Scene data for correlation
- Audio Analysis Team: Audio emotion scores

**Provide To:**
- Frontend Team: Sentiment JSON, topics, metrics
- Prediction Engine: Sentiment scores for final prediction
- Database: Store analysis results

---

**Good luck! පුරුදු වෙන් ගිහිරුවතින් සාර්ථකයි! 🚀**
