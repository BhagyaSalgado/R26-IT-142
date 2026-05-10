# Comment Sentiment Analysis - Frontend Integration Guide

## 📱 Frontend Components Added

### 1. **CommentAnalysisCharts.tsx**
Visual components for displaying comment analysis results.

#### Components:
- **CommentTopicsChart** - Horizontal bar chart showing discussion topics
- **RegionalInterestChart** - Pie chart showing geographic distribution

```tsx
import { CommentTopicsChart, RegionalInterestChart } from './components/CommentAnalysisCharts';

// Usage
<CommentTopicsChart result={analysis} />
<RegionalInterestChart result={analysis} />
```

### 2. **CommentInsights.tsx**
Display key insights and metrics from sentiment analysis.

#### Features:
- Total comments count
- Sentiment dominance indicator
- Key insights generation
- Top discussion topics display

```tsx
import { CommentInsights } from './components/CommentInsights';

<CommentInsights analysis={analysis} />
```

### 3. **sentimentApi.ts**
Service layer for calling backend sentiment analysis APIs.

#### Available Functions:

```typescript
// Main sentiment analysis
analyzeCommentSentiment(request: CommentAnalysisRequest): Promise<CommentAnalysisResponse>

// Get comment topics
getCommentTopics(trailerId: string): Promise<Array<{ topic: string; mentions: number }>>

// Get regional distribution
getRegionalDistribution(trailerId: string): Promise<Array<{ region: string; value: number }>>

// Get sentiment metrics
getSentimentMetrics(trailerId: string): Promise<{ sentiment: {...}, metrics: {...} }>

// Get individual comments
getCommentDetails(trailerId: string, limit?: number): Promise<Array<{ id, text, sentiment, confidence, language, likes }>>
```

---

## 🔌 Backend API Endpoints Required

Your backend must provide these endpoints:

### 1. **POST /api/sentiment/analyze**
Main sentiment analysis endpoint.

**Request:**
```json
{
  "trailer_url": "https://youtube.com/watch?v=...",
  "trailer_title": "Movie Trailer Name"
}
```

**Response:**
```json
{
  "sentiment": {
    "positive": 64,
    "neutral": 22,
    "negative": 14
  },
  "commentTopics": [
    { "topic": "Lead actor", "mentions": 4200 },
    { "topic": "Background music", "mentions": 3100 }
  ],
  "regionalInterest": [
    { "region": "United States", "value": 31 },
    { "region": "India", "value": 22 }
  ],
  "totalComments": 18400,
  "modelMetrics": {
    "accuracy": 0.87,
    "precision": 0.89,
    "recall": 0.85,
    "f1Score": 0.87
  }
}
```

### 2. **GET /api/sentiment/topics/{trailerId}**
Get comment topics for a specific trailer.

**Response:**
```json
{
  "topics": [
    { "topic": "Actors", "mentions": 345 },
    { "topic": "Music", "mentions": 298 }
  ]
}
```

### 3. **GET /api/sentiment/regional-distribution/{trailerId}**
Get regional audience distribution.

**Response:**
```json
{
  "regions": [
    { "region": "United States", "value": 31 },
    { "region": "India", "value": 22 }
  ]
}
```

### 4. **GET /api/sentiment/metrics/{trailerId}**
Get detailed sentiment metrics.

**Response:**
```json
{
  "sentiment": {
    "positive": 64,
    "neutral": 22,
    "negative": 14
  },
  "metrics": {
    "accuracy": 0.87,
    "precision": 0.89,
    "recall": 0.85,
    "f1Score": 0.87
  }
}
```

### 5. **GET /api/sentiment/comments/{trailerId}?limit=50**
Get individual comments with sentiment labels.

**Response:**
```json
{
  "comments": [
    {
      "id": "comment_001",
      "text": "Amazing trailer! Can't wait!",
      "sentiment": "positive",
      "confidence": 0.95,
      "language": "en",
      "likes": 150
    }
  ]
}
```

---

## 📊 Data Flow Integration

```
┌─────────────────────────────────────────────────────────┐
│              Frontend Application                         │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │ App.tsx (Dashboard View)                          │   │
│  │                                                   │   │
│  │  ├─ MetricCard (displays sentiment %)            │   │
│  │  ├─ SentimentChart (pie chart)                   │   │
│  │  ├─ CommentTopicsChart (bar chart)               │   │
│  │  ├─ RegionalInterestChart (pie chart)            │   │
│  │  └─ CommentInsights (key insights)               │   │
│  └──────────────────────────────────────────────────┘   │
│           ↓                                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │ sentimentApi.ts (Service Layer)                   │   │
│  │                                                   │   │
│  │  - analyzeCommentSentiment()                     │   │
│  │  - getCommentTopics()                           │   │
│  │  - getRegionalDistribution()                    │   │
│  │  - getSentimentMetrics()                        │   │
│  │  - getCommentDetails()                          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
           ↓ HTTP Requests
┌─────────────────────────────────────────────────────────┐
│           Backend API (Your Implementation)              │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │ /api/sentiment/* endpoints                        │   │
│  │                                                   │   │
│  │  ├─ YouTube API Integration                      │   │
│  │  ├─ Text Preprocessing (NLTK/spaCy)             │   │
│  │  ├─ BERT Model (Hugging Face)                   │   │
│  │  ├─ Topic Extraction                            │   │
│  │  ├─ Language Detection                          │   │
│  │  └─ MongoDB Database                            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🎨 Dashboard Integration

### Added Sections to Dashboard:

#### 1. **Comment Topics Section**
- Location: After "Top feature contributions"
- Size: 2 columns (lg), full width (md/sm)
- Component: `CommentTopicsChart`
- Data Source: `analysis.commentTopics`

#### 2. **Regional Interest Section**
- Location: Same row as Comment Topics
- Size: 1 column (lg)
- Component: `RegionalInterestChart`
- Data Source: `analysis.regionalInterest`

#### 3. **Comment Insights Section**
- Location: Below Comment Topics and Regional Interest
- Size: Full width (3 columns)
- Component: `CommentInsights`
- Features:
  - Total comments display
  - Sentiment dominance
  - Auto-generated insights
  - Top discussion topics

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Sentiment Analysis API
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_SENTIMENT_API_TIMEOUT=30000
REACT_APP_SENTIMENT_MODEL_VERSION=bert-base
```

### API Client Configuration

The sentiment API client uses:
- Base URL: `process.env.REACT_APP_API_URL` (default: `http://localhost:5000/api`)
- Timeout: 30 seconds
- Content-Type: `application/json`

---

## 📝 Type Definitions

### AnalysisResult Type
```typescript
interface AnalysisResult {
  sentiment: SentimentDistribution;
  commentTopics: Array<{ topic: string; mentions: number }>;
  regionalInterest: Array<{ region: string; value: number }>;
  modelMetrics: Array<{ metric: string; value: number }>;
  // ... other fields
}

interface SentimentDistribution {
  positive: number;  // 0-100
  neutral: number;   // 0-100
  negative: number;  // 0-100
}
```

---

## 🚀 Usage Examples

### Basic Integration
```tsx
import { analyzeCommentSentiment } from './services/sentimentApi';
import { CommentInsights } from './components/CommentInsights';

function MyComponent() {
  const [analysis, setAnalysis] = useState<AnalysisResult>(mockData);

  const handleAnalyze = async () => {
    try {
      const result = await analyzeCommentSentiment({
        trailerUrl: 'https://youtube.com/watch?v=...',
        trailerTitle: 'My Movie Trailer'
      });
      
      // Update analysis with sentiment results
      setAnalysis(prev => ({
        ...prev,
        sentiment: result.sentiment,
        commentTopics: result.commentTopics,
        regionalInterest: result.regionalInterest
      }));
    } catch (error) {
      console.error('Analysis failed:', error);
    }
  };

  return (
    <div>
      <button onClick={handleAnalyze}>Analyze</button>
      <CommentInsights analysis={analysis} />
    </div>
  );
}
```

### Get Comment Topics
```tsx
async function fetchTopics(trailerId: string) {
  try {
    const topics = await getCommentTopics(trailerId);
    console.log('Topics:', topics);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

### Get Regional Distribution
```tsx
async function fetchRegions(trailerId: string) {
  try {
    const regions = await getRegionalDistribution(trailerId);
    console.log('Regional distribution:', regions);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

## 📊 Metrics Tracking

The frontend tracks and displays:

### Sentiment Metrics
- **Positive %**: Percentage of positive comments
- **Neutral %**: Percentage of neutral comments
- **Negative %**: Percentage of negative comments

### Discussion Topics
- Topic name
- Number of mentions

### Regional Interest
- Region/Country name
- Percentage of audience

### Model Performance
- **Accuracy**: Overall correctness (0-1)
- **Precision**: True positive rate (0-1)
- **Recall**: Sensitivity (0-1)
- **F1-Score**: Harmonic mean of precision & recall (0-1)

---

## ✨ Features Implemented

✅ Sentiment distribution visualization (pie chart)  
✅ Discussion topics visualization (bar chart)  
✅ Regional audience distribution (pie chart)  
✅ Key insights generation  
✅ Total comments display  
✅ Sentiment dominance indicator  
✅ API service layer  
✅ Responsive design  
✅ Error handling  
✅ Mock data support  

---

## 🔄 State Management

The `AnalysisResult` state in App.tsx includes all comment analysis data:

```tsx
const [analysis, setAnalysis] = useState<AnalysisResult>(mockAnalysisResult);

// All components receive this analysis object and extract relevant data
<MetricCard value={`${analysis.sentiment.positive}%`} />
<SentimentChart result={analysis} />
<CommentTopicsChart result={analysis} />
<RegionalInterestChart result={analysis} />
<CommentInsights analysis={analysis} />
```

---

## 📦 Dependencies Used

```json
{
  "recharts": "^2.x.x",      // Charting library
  "lucide-react": "^0.x.x",  // Icons
  "framer-motion": "^10.x.x" // Animations
}
```

---

## 🎯 Next Steps for Backend Implementation

1. **Set up Flask/FastAPI server**
   ```python
   from flask import Flask
   app = Flask(__name__)
   
   @app.route('/api/sentiment/analyze', methods=['POST'])
   def analyze_sentiment():
       # Your implementation
       pass
   ```

2. **Implement BERT model loading**
   ```python
   from transformers import pipeline
   sentiment = pipeline("sentiment-analysis", model="bert-base-uncased")
   ```

3. **Integrate YouTube API**
   ```python
   from googleapiclient.discovery import build
   youtube = build('youtube', 'v3', developerKey=API_KEY)
   ```

4. **Implement text preprocessing**
   ```python
   import nltk
   from nltk.corpus import stopwords
   # Implement preprocessing pipeline
   ```

5. **Set up MongoDB**
   ```python
   from pymongo import MongoClient
   client = MongoClient('mongodb://...')
   ```

6. **Deploy to cloud**
   - AWS EC2, Google Cloud, or Azure
   - Set up environment variables
   - Configure CORS for frontend

---

## 🐛 Troubleshooting

### API Connection Issues
- Check `REACT_APP_API_URL` environment variable
- Verify backend server is running
- Check CORS headers in backend

### Chart Not Displaying
- Verify `commentTopics` and `regionalInterest` arrays are populated
- Check browser console for errors
- Ensure Recharts library is installed

### Sentiment Metrics Not Updating
- Verify API response format matches expected interface
- Check network tab in browser dev tools
- Verify data is being passed to components correctly

---

## 📚 References

- [BERT Model Documentation](https://huggingface.co/bert-base-uncased)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Recharts Documentation](https://recharts.org/)
- [Flask API Documentation](https://flask.palletsprojects.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)

---

**Frontend Integration Status: ✅ Complete**  
**Awaiting Backend Implementation: ⏳ Pending**

Last Updated: May 6, 2026
