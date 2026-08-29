# Prediction Flow - How It Works

## 📊 Current System Architecture

### Current State: **DUMMY DATA** ✅

```
┌─────────────────────────────────────────────────────────┐
│                 Frontend (React)                         │
│                                                          │
│  User clicks "Analyze" or visits Dashboard              │
│           ↓                                              │
│  ┌─────────────────────────────────┐                    │
│  │ App.tsx                         │                    │
│  │                                 │                    │
│  │ useState<AnalysisResult> =      │                    │
│  │   mockAnalysisResult ✨         │                    │
│  │                                 │                    │
│  │ This is DUMMY DATA from:        │                    │
│  │ data/mockBackend.ts             │                    │
│  └─────────────────────────────────┘                    │
│           ↓                                              │
│  ┌─────────────────────────────────┐                    │
│  │ Render Dashboard                │                    │
│  │                                 │                    │
│  │ • MetricCards                   │                    │
│  │ • SentimentChart                │                    │
│  │ • CommentTopicsChart            │                    │
│  │ • RegionalInterestChart         │                    │
│  │ • CommentInsights               │                    │
│  └─────────────────────────────────┘                    │
│           ↓                                              │
│  ✅ Display on Screen with Mock Data                    │
│                                                          │
└─────────────────────────────────────────────────────────┘

No Backend 🚫 | No API Calls 🚫 | No Real Data 🚫
```

---

## 📝 Dummy Data Structure

### mockAnalysisResult (src/data/mockBackend.ts)

```typescript
{
  id: 'ANL-2026-0427',
  trailerTitle: 'Shadow Horizon - Official Trailer',
  sourceUrl: 'https://youtube.com/watch?v=dummy-trailer',
  generatedAt: '2026-05-02 12:38',
  
  // ✨ Comment Sentiment Analysis Part
  sentiment: {
    positive: 64,      // YOUR BERT MODEL will generate this
    neutral: 22,
    negative: 14
  },
  
  commentTopics: [      // YOUR TOPIC EXTRACTION will generate this
    { topic: 'Lead actor', mentions: 4200 },
    { topic: 'Background music', mentions: 3100 },
    { topic: 'Visual effects', mentions: 2850 }
  ],
  
  regionalInterest: [   // YOUR LANGUAGE DETECTION will generate this
    { region: 'United States', value: 31 },
    { region: 'India', value: 22 },
    { region: 'United Kingdom', value: 16 }
  ],
  
  modelMetrics: [       // YOUR MODEL EVALUATION will generate this
    { metric: 'Accuracy', value: 88 },
    { metric: 'Precision', value: 84 },
    { metric: 'Recall', value: 82 },
    { metric: 'F1-score', value: 85 }
  ]
}
```

---

## 🔄 Flow Comparison: Current vs Future

### CURRENT (With Dummy Data)
```
Frontend Dashboard
   ↓
App.tsx loads mockAnalysisResult
   ↓
Components render with dummy data
   ↓
Charts show hardcoded values
   ✅ Works immediately (for demo)
   ❌ Not real analysis
```

### FUTURE (With Backend)
```
User uploads trailer URL
   ↓
Frontend calls: analyzeCommentSentiment(trailerUrl)
   ↓
sentimentApi.ts: POST /api/sentiment/analyze
   ↓ HTTP Request
Backend (Flask/Python)
   ├─ YouTube API → Fetch comments
   ├─ Preprocessor → Clean text
   ├─ Language Detector → Identify language
   ├─ BERT Model → Classify sentiment
   ├─ Topic Extractor → Extract topics
   └─ Return JSON response
   ↓ HTTP Response
Frontend receives real data
   ↓
Update state: setAnalysis(realData)
   ↓
Components re-render with REAL analysis
   ✅ Shows actual audience sentiment!
```

---

## 🎮 How to Test Current System

### Option 1: View Dummy Data (Current)
```
1. Run: npm run dev
2. Open: http://localhost:5173
3. See Dashboard with dummy data
4. Everything displays perfectly!
```

### Option 2: Modify Dummy Data
Edit `src/data/mockBackend.ts`:

```typescript
sentiment: {
  positive: 75,   // Change from 64 to 75
  neutral: 15,
  negative: 10
}
```

Then see dashboard update immediately! ✨

### Option 3: Try "Analyze" Button
```
1. Click "Analyze trailer" tab
2. Try uploading a video
3. Nothing happens (no backend)
4. Check console: API error
```

---

## 📡 Analyze Button Flow (Currently)

### What Happens Now:

```typescript
// In UploadPanel.tsx
const handleAnalyze = async () => {
  // Tries to call backend...
  const response = await analyzeCommentSentiment({
    trailerUrl: userInput,
    trailerTitle: userInput
  });
  
  // Backend doesn't exist, so:
  // ❌ Network Error
  // ❌ Connection Refused
  // ❌ Error: Failed to fetch
}
```

### Simulated Response (Expected):

```json
{
  "sentiment": {
    "positive": 64,
    "neutral": 22,
    "negative": 14
  },
  "commentTopics": [
    { "topic": "Lead actor", "mentions": 4200 }
  ],
  "regionalInterest": [
    { "region": "United States", "value": 31 }
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

---

## 🛠️ Option: Create Mock Backend Server

### mockServer.ts (For Testing)

```typescript
// This simulates backend responses for testing

export function createMockResponse(trailerUrl: string) {
  // Simulate different responses based on URL
  const urlHash = trailerUrl.length % 10;
  
  const responses = [
    {
      sentiment: { positive: 75, neutral: 15, negative: 10 },
      commentTopics: [
        { topic: 'Lead actor', mentions: 5200 },
        { topic: 'Music', mentions: 3800 }
      ]
    },
    {
      sentiment: { positive: 45, neutral: 30, negative: 25 },
      commentTopics: [
        { topic: 'Plot', mentions: 2100 },
        { topic: 'Dialogue', mentions: 1800 }
      ]
    },
    // ... more scenarios
  ];
  
  return responses[urlHash];
}
```

Then in sentimentApi.ts:

```typescript
export async function analyzeCommentSentiment(
  request: CommentAnalysisRequest
): Promise<CommentAnalysisResponse> {
  // Mock mode (for testing without backend)
  if (process.env.REACT_APP_USE_MOCK === 'true') {
    await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate delay
    return createMockResponse(request.trailerUrl);
  }
  
  // Real API call (when backend ready)
  try {
    const response = await fetch(`${API_BASE_URL}/sentiment/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trailer_url: request.trailerUrl,
        trailer_title: request.trailerTitle,
      }),
    });
    // ... rest of implementation
  }
}
```

---

## 📊 Dummy Data vs Real Data

| Aspect | Dummy (Current) | Real (Backend) |
|--------|---|---|
| **Source** | Hardcoded in mockBackend.ts | YouTube API |
| **Comment Text** | Fake | Real YouTube comments |
| **Sentiment** | Random values | BERT model classification |
| **Topics** | Predetermined | Extracted from comments |
| **Regions** | Predefined | Language detection |
| **Accuracy** | N/A | 85%+ BERT model accuracy |
| **Speed** | Instant | 2-5 seconds per trailer |
| **Cost** | Free | API calls cost |

---

## 🚀 How to Switch to Real Backend

### Step 1: Backend Ready
```python
# Your Flask server running
python app.py
# Server at: http://localhost:5000
```

### Step 2: Update Frontend .env
```env
REACT_APP_API_URL=http://localhost:5000/api
```

### Step 3: Remove Mock Data (Optional)
```typescript
// In App.tsx
- const [analysis, setAnalysis] = useState<AnalysisResult>(mockAnalysisResult);
+ const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
```

### Step 4: Call Real Backend
```typescript
// sentimentApi.ts automatically calls backend
const result = await analyzeCommentSentiment({
  trailerUrl: 'https://youtube.com/watch?v=...',
  trailerTitle: 'Movie Name'
});

// Real data from BERT model, YouTube API, etc.
```

### Step 5: Test
```
1. Upload trailer URL
2. Wait for analysis
3. See REAL sentiment analysis!
```

---

## 📋 Current Data Flow Diagram

```
┌──────────────────────────────────────────────────────────┐
│                     FRONTEND (Now)                        │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │ App.tsx                                            │  │
│  │ const [analysis] = useState(mockAnalysisResult)   │  │
│  └────────────────────────────────────────────────────┘  │
│           ↓ (No API call, just use state)                │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Components Receive Props                          │  │
│  │ • analysis.sentiment                              │  │
│  │ • analysis.commentTopics                          │  │
│  │ • analysis.regionalInterest                       │  │
│  └────────────────────────────────────────────────────┘  │
│           ↓                                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Render Charts                                      │  │
│  │ • Sentiment: 64% positive                         │  │
│  │ • Topics: Lead actor 4200 mentions                │  │
│  │ • Regions: USA 31%, India 22%                     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 For Your Team Presentation

### Explain Current State:
"Currently the frontend is fully functional with mock data from our project specifications. Once the backend Comment Sentiment Analysis component is complete, it will replace this mock data with real analysis from BERT model, YouTube API, and NLP processing."

### Show This Diagram:
```
PHASE 1 (Now):  Frontend + Mock Data ✅
                ↓
PHASE 2 (Next): Backend Implementation 🚀
                ↓
PHASE 3 (Final): Frontend ↔ Backend Integration ✨
```

---

## 💡 Key Points

✅ **What's Working:**
- Frontend renders perfectly
- All components display
- Charts show beautiful data
- UI/UX fully implemented

⏳ **What's Waiting:**
- Backend implementation
- Real BERT model
- YouTube API integration
- Real analysis results

🔗 **How They Connect:**
- sentimentApi.ts ready to call backend
- JSON response format defined
- Components ready to display real data
- Just need backend to fill in

---

## 📞 If Asked "Is This Real?"

**Answer:**
> "No, this is using simulated/dummy data for UI demonstration. The frontend is completely built and ready. Once the backend Comment Sentiment Analysis component is implemented with BERT model and YouTube API integration, this will display real sentiment analysis, actual audience topics, and genuine regional distribution data."

---

## 🎓 Summary

### Current System (Dummy Data)
```
✅ Frontend complete
✅ UI/UX beautiful
✅ Charts working
✅ Responsive design
❌ No real analysis
❌ No backend
❌ No API calls
```

### Future System (Real Data)
```
✅ Frontend complete
✅ Backend API
✅ BERT Model
✅ YouTube Integration
✅ Real sentiment analysis
✅ Actual regional data
✅ Genuine topic extraction
```

Your job: Build the backend! 🚀

---

Last Updated: May 6, 2026
