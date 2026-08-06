"""
Firebase Configuration Guide
"""

FIREBASE_SETUP_GUIDE = """
🔥 Firebase Setup Instructions

1. CREATE FIREBASE PROJECT
   - Go to https://console.firebase.google.com
   - Click "Create Project" or "Add Project"
   - Enter project name (e.g., "movie-sentiment-analyzer")
   - Create project

2. ENABLE REALTIME DATABASE
   - In Firebase Console, go to "Realtime Database"
   - Click "Create Database"
   - Start in "Test Mode" (for development)
   - Select region closest to you
   - Create database

3. CREATE SERVICE ACCOUNT & GET CREDENTIALS
   - Go to Project Settings (gear icon)
   - Click "Service Accounts" tab
   - Click "Generate New Private Key"
   - Save the JSON file as "firebase-config.json"
   - Place in project root directory

4. UPDATE .env FILE
   - Open .env file
   - Find FIREBASE_CREDENTIALS line
   - Make sure it points to: ./firebase-config.json
   - Find FIREBASE_DATABASE_URL
   - Copy your database URL from Firebase Console
   - It should look like: https://your-project.firebaseio.com

5. SET DATABASE RULES (for development)
   - In Firebase Console, go to "Realtime Database"
   - Click "Rules" tab
   - Replace with:
   
   {
     "rules": {
       ".read": true,
       ".write": true
     }
   }
   
   ⚠️  WARNING: These are open rules for DEVELOPMENT ONLY
       For production, implement proper security rules!

6. TEST CONNECTION
   - Run: python quick_test.py
   - Should show ✅ Firebase connection successful

📁 File Structure After Setup:

movie-trailer-analyzer-backend/
├── firebase-config.json        ← Add your credentials here
├── .env                        ← Update with your URLs
└── ... (other files)

Example .env entries:
FIREBASE_CREDENTIALS=./firebase-config.json
FIREBASE_DATABASE_URL=https://movie-sentiment-analyzer.firebaseio.com

Once set up, Firebase automatically saves all analysis results!
"""

if __name__ == '__main__':
    print(FIREBASE_SETUP_GUIDE)
