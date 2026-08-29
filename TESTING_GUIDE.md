# Testing Guide - Using Mock Data vs Real Backend

## 🎮 How to Test the System

### Option 1: Using Current Dummy Data (DEFAULT)
**Status:** ✅ Working now  
**Data Source:** `src/data/mockBackend.ts`  
**API Calls:** None

```bash
npm run dev
# Open http://localhost:5173
# See dashboard with hardcoded dummy data
```

---

### Option 2: Using Mock Server (FOR TESTING)
**Status:** ⏳ Available soon  
**Data Source:** `src/services/mockServer.ts`  
**API Calls:** Simulated with delay

#### Setup:

1. **Create .env.local file:**
```env
REACT_APP_API_URL=http://localhost:5000
REACT_APP_USE_MOCK=true
REACT_APP_MOCK_DELAY=1500
```

2. **Update sentimentApi.ts to use mock:**
```typescript
import { mockAnalyzeCommentSentiment } from './mockServer';

export async function analyzeCommentSentiment(request: CommentAnalysisRequest) {
  // Use mock server if enabled
  if (process.env.REACT_APP_USE_MOCK === 'true') {
    return await mockAnalyzeCommentSentiment(request.trailerUrl);
  }
  
  // Otherwise use real backend
  // ... real API call
}
```

3. **Test scenarios:**
```
Try these URLs in "Analyze" tab:
- https://youtube.com/watch?v=positive-trailer     → 72% positive
- https://youtube.com/watch?v=mixed-trailer        → Mixed sentiment
- https://youtube.com/watch?v=negative-trailer     → 47% negative
- https://youtube.com/watch?v=anything-else        → Random response
```

---

### Option 3: Using Real Backend (FUTURE)
**Status:** 🚀 When backend is ready  
**Data Source:** Python/Flask backend  
**API Calls:** Real HTTP requests

#### Setup:

1. **Backend running:**
```bash
python app.py  # On port 5000
```

2. **Frontend .env:**
```env
REACT_APP_API_URL=http://localhost:5000
REACT_APP_USE_MOCK=false
```

3. **Upload real YouTube trailer:**
```
Analyze → Enter YouTube URL → Wait 3-5 seconds → See real analysis!
```

---

## 📊 Comparison

| Feature | Dummy Data | Mock Server | Real Backend |
|---------|-----------|-------------|--------------|
| **Setup** | None | 1 line code | Backend + Python |
| **Speed** | Instant | Simulated delay | Real processing |
| **Realism** | Hardcoded | Simulated but varied | 100% real |
| **Data Source** | mockBackend.ts | mockServer.ts | BERT + YouTube API |
| **Good For** | Quick demo | Testing flow | Production |
| **API Calls** | None | None (simulated) | Real HTTP |

---

## 🎯 Current Prediction Flow

### In Dashboard (NO Backend)
```
1. App loads
2. useState(mockAnalysisResult)
3. Components render with dummy data
4. Charts display hardcoded values
5. No API calls made ✅ (Fast)
```

### With Mock Server (TESTING)
```
1. User clicks "Analyze"
2. sentimentApi.analyzeCommentSentiment()
3. Checks: is REACT_APP_USE_MOCK true?
4. YES → Call mockServer functions
5. Simulate 1.5s delay
6. Return mock response
7. Update state with mock analysis
8. Components re-render ✅ (Realistic flow)
```

### With Real Backend (PRODUCTION)
```
1. User enters trailer URL
2. sentimentApi.analyzeCommentSentiment()
3. Checks: is REACT_APP_USE_MOCK true?
4. NO → Call real backend
5. Backend:
   - Fetch comments from YouTube
   - Preprocess text
   - Run BERT model
   - Extract topics
   - Return analysis
6. Frontend receives real data
7. Components display real sentiment ✅ (Production)
```

---

## 🧪 Testing Checklist

### Dashboard View (Current - Works!)
- [ ] Page loads
- [ ] Sentiment chart shows 64% positive
- [ ] Comment topics display
- [ ] Regional chart shows USA 31%
- [ ] Metrics cards show data
- [ ] All charts render correctly

### Mock Server Testing (When Ready)
- [ ] Set `REACT_APP_USE_MOCK=true`
- [ ] Click "Analyze trailer" tab
- [ ] Enter positive-trailer URL
- [ ] See loading state for 1.5s
- [ ] Sentiment updates to mock data
- [ ] Charts re-render with new data
- [ ] Try negative-trailer URL
- [ ] See different sentiment
- [ ] Try mixed-trailer URL
- [ ] See balanced sentiment

### Real Backend Testing (Future)
- [ ] Start Flask backend
- [ ] Set `REACT_APP_USE_MOCK=false`
- [ ] Enter real YouTube trailer URL
- [ ] See loading indicator
- [ ] Wait for processing (3-5s)
- [ ] See REAL sentiment analysis
- [ ] Charts show REAL audience reaction
- [ ] Comments displayed with confidence
- [ ] Topics match actual discussions
- [ ] Regional distribution matches languages

---

## 💻 Console Testing

### Check if Mock Mode Enabled
```javascript
// Open browser console (F12)
console.log(process.env.REACT_APP_USE_MOCK);
// Should print: "true" or "false"
```

### Test Mock Scenarios
```javascript
import { listMockScenarios } from './services/mockServer';

// List available test URLs
listMockScenarios();
```

Output:
```
Available Mock Scenarios:
  positive: Positive Reception
    URL: https://youtube.com/watch?v=positive-trailer
    72% positive sentiment
  
  mixed: Mixed Reception
    URL: https://youtube.com/watch?v=mixed-trailer
    48% positive, 32% neutral, 20% negative
  
  negative: Negative Reception
    URL: https://youtube.com/watch?v=negative-trailer
    47% negative sentiment
```

---

## 🔍 How to Debug

### Check Current Data Source
```typescript
// In App.tsx
console.log('Using mock:', process.env.REACT_APP_USE_MOCK);
console.log('Analysis data:', analysis);
```

### Monitor API Calls
```typescript
// In sentimentApi.ts
console.log('Calling endpoint:', `${API_BASE_URL}/sentiment/analyze`);
```

### Check Network Tab (Browser DevTools)
- **Dummy Data Mode:** No network requests
- **Mock Server Mode:** No network requests (simulated)
- **Real Backend:** Network requests to localhost:5000

---

## 📋 File Structure for Testing

```
src/
├── data/
│   └── mockBackend.ts          ← Dummy data (Current)
├── services/
│   ├── sentimentApi.ts         ← API calls (Updated)
│   └── mockServer.ts           ← Mock responses (New)
├── components/
│   ├── CommentAnalysisCharts   ← Displays data
│   ├── CommentInsights         ← Displays data
│   └── ...
└── App.tsx                     ← Uses data
```

---

## 🚀 Migration Path

### Phase 1 (NOW ✅)
- Dummy data from mockBackend.ts
- Dashboard displays perfectly
- No backend needed

### Phase 2 (NEXT 📋)
- Backend implementation starts
- Keep dummy data as fallback
- Set REACT_APP_USE_MOCK=true for testing
- Use mock server to validate flow

### Phase 3 (FUTURE 🚀)
- Backend complete
- Set REACT_APP_USE_MOCK=false
- Real API calls to backend
- Production deployment

---

## 📝 For Your Presentation

### Show This Slide:
```
Current State (May 6, 2026):
✅ Frontend Complete with Dummy Data
✅ Charts and Components Working
⏳ Backend Implementation In Progress
🚀 Mock Server Ready for Testing
```

### Explain:
"The frontend is fully functional with simulated data for demonstration. Once the backend is implemented, we'll connect it by simply changing an environment variable and the system will use real BERT sentiment analysis, actual YouTube comments, and genuine regional distribution data."

---

## ✅ When Everything Is Ready

All components will work with REAL data:

```
YouTube Trailer URL
   ↓ (User input)
   ↓
Frontend
   ↓ (API call)
   ↓
Backend
   ├─ YouTube API → Comments
   ├─ BERT Model → Sentiment
   ├─ Topic Extractor → Topics
   └─ Language Detector → Regions
   ↓ (JSON response)
   ↓
Frontend receives:
{
  "sentiment": {
    "positive": 64,    ← REAL from BERT
    "neutral": 22,
    "negative": 14
  },
  "commentTopics": [   ← REAL from comments
    { "topic": "Lead actor", "mentions": 4200 }
  ],
  "regionalInterest": [ ← REAL from language detection
    { "region": "United States", "value": 31 }
  ]
}
   ↓
Dashboard updates with REAL analysis! 🎉
```

---

**Summary:**
- **Dummy data:** ✅ Works now, great for demo
- **Mock server:** ⏳ Available for realistic testing
- **Real backend:** 🚀 Your implementation will complete the system

Start with Option 1 (dummy data), test with Option 2 (mock) when ready, deploy with Option 3 (real backend)! 🚀
