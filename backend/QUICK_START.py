"""
QUICK START - Follow this to get everything running
"""

QUICK_START = """
⚡ QUICK START GUIDE - 10 Minutes to Running Backend

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: SETUP ENVIRONMENT (Windows)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Open Command Prompt
2. Navigate to backend folder:
   cd C:\\Users\\YOUR_NAME\\OneDrive\\Desktop\\movie-trailer-analyzer-backend

3. Run setup script:
   setup.bat

   Wait for completion (~3-5 minutes)

(For Mac/Linux: bash setup.sh)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: CONFIGURE (.env file)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Open .env file in your editor
2. Update these values:

   FIREBASE_CREDENTIALS=./firebase-config.json
   FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
   SECRET_KEY=any-random-string-here

3. Save file

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: FIREBASE CREDENTIALS (if using Firebase)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to https://console.firebase.google.com
2. Create new project or use existing
3. Download service account JSON
4. Save as: firebase-config.json in project root

(Or run: python FIREBASE_SETUP.py for detailed guide)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: PREPARE DATASET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Place finalized_movie_info.xlsx in data/ folder
2. Run cleaning script:
   python scripts/clean_dataset.py

3. Check data/cleaned_comments.csv was created

(Or run: python DATASET_GUIDE.py for detailed guide)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5: RUN QUICK TEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python quick_test.py

Should show:
✅ All tests passed! Backend is ready to run.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6: START BACKEND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python app.py

You should see:
🚀 Starting Comment Sentiment Analysis Backend
✅ Flask server running on http://localhost:5000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 7: TEST API ENDPOINTS (new terminal)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Keep backend running (Step 6), then in new terminal:

python test_api.py

Should show test results for all endpoints

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 8: FRONTEND INTEGRATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend is now running at: http://localhost:5000

Frontend will send requests to: /api/sentiment/analyze

Make sure frontend .env has:
REACT_APP_API_URL=http://localhost:5000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 ADDITIONAL COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View setup guide:
  python FIREBASE_SETUP.py

View dataset guide:
  python DATASET_GUIDE.py

Run tests:
  python tests/test_sentiment_service.py

Clean dataset again:
  python scripts/clean_dataset.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 FOLDER STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
movie-trailer-analyzer-backend/
├── app.py                      ← Main server
├── requirements.txt            ← Dependencies
├── setup.bat                   ← Windows setup
├── setup.sh                    ← Mac/Linux setup
├── quick_test.py              ← Test script
├── test_api.py                ← API test
├── .env                        ← Configuration (UPDATE THIS!)
├── firebase-config.json        ← Credentials (DOWNLOAD THIS!)
│
├── config/                    ← Settings & constants
├── models/                    ← ML models
├── services/                  ← Business logic
├── api/                       ← API routes
├── utils/                     ← Utilities
├── scripts/                   ← Helper scripts
│   └── clean_dataset.py       ← Data cleaning
├── tests/                     ← Tests
├── data/                      ← Your Excel file & cleaned data
└── logs/                      ← Log files

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ WHEN DONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Backend running on http://localhost:5000
✓ API endpoints responding
✓ Firebase saving data
✓ Dataset cleaned and ready
✓ Frontend can connect and get sentiment analysis

🎉 COMPLETE!
"""

if __name__ == '__main__':
    print(QUICK_START)
