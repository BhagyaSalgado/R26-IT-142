"""Firebase Database Service"""

import logging
import os
import firebase_admin
from firebase_admin import credentials, db, firestore
from config.settings import FIREBASE_CREDENTIALS, FIREBASE_DATABASE_URL
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FirebaseService:
    """Firebase database operations, with an in-memory fallback when Firebase isn't configured"""
    
    def __init__(self):
        self.app = None
        self.db = None
        self.firestore_db = None
        # In-memory fallback store so /analyze and /analyze/<id> still work without Firebase credentials
        self._memory_analyses: Dict[str, Dict] = {}
        self._memory_comments: List[Dict] = []
        self.initialize_firebase()

    @property
    def mode(self) -> str:
        if self.db:
            return 'firebase-realtime'
        if self.firestore_db:
            return 'firebase-firestore'
        return 'memory'
    
    def initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            # Check if Firebase credentials exist
            if not os.path.exists(FIREBASE_CREDENTIALS):
                logger.warning(f"⚠️  Firebase credentials not found: {FIREBASE_CREDENTIALS}")
                logger.warning("⚠️  Firebase features will be disabled")
                logger.warning("To enable Firebase, download credentials from Firebase Console and save as firebase-config.json")
                self.db = None
                return
            
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self.app = firebase_admin._apps[0]
                logger.info("✅ Using existing Firebase connection")
            else:
                # Initialize new connection
                cred = credentials.Certificate(FIREBASE_CREDENTIALS)
                options = {'databaseURL': FIREBASE_DATABASE_URL} if FIREBASE_DATABASE_URL else None
                self.app = firebase_admin.initialize_app(cred, options=options)
                logger.info("✅ Firebase initialized successfully")

            # Firestore works without Realtime Database URL.
            self.firestore_db = firestore.client(self.app)

            # Realtime Database is optional for this backend.
            self.db = db if FIREBASE_DATABASE_URL else None
            if not FIREBASE_DATABASE_URL:
                logger.info("ℹ️  FIREBASE_DATABASE_URL not set; using Firestore mode")
        except Exception as e:
            logger.warning(f"⚠️  Firebase initialization failed: {str(e)}")
            logger.warning("⚠️  Backend will work without Firebase")
            self.db = None
            self.firestore_db = None
    
    def save_analysis_result(self, trailer_id: str, analysis_data: Dict, trailer_title: str = '') -> bool:
        """
        Save sentiment analysis result to Firebase
        
        Args:
            trailer_id: Unique trailer identifier
            analysis_data: Analysis results
            trailer_title: Optional human-readable trailer title
            
        Returns:
            True if successful, False otherwise
        """
        result_data = {
            **analysis_data,
            'trailer_id': trailer_id,
            'trailer_title': trailer_title,
            'timestamp': datetime.now().isoformat(),
            'saved': True
        }
        # Always keep an in-memory copy so history/cached reads still work
        # even if Firebase calls fail intermittently.
        self._memory_analyses[trailer_id] = result_data

        if not self.db and not self.firestore_db:
            logger.info(f"✅ Saved analysis for trailer (memory mode): {trailer_id}")
            return True

        try:
            if self.db:
                # Save to Firebase Realtime Database
                self.db.reference(f'analyses/{trailer_id}').set(result_data)
                logger.info(f"✅ Saved analysis for trailer (realtime): {trailer_id}")
            elif self.firestore_db:
                # Save to Firestore
                self.firestore_db.collection('analyses').document(trailer_id).set(result_data)
                logger.info(f"✅ Saved analysis for trailer (firestore): {trailer_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error saving to Firebase, kept in memory fallback: {str(e)}")
            return True
    
    def get_analysis_result(self, trailer_id: str) -> Optional[Dict]:
        """
        Retrieve saved analysis result
        
        Args:
            trailer_id: Unique trailer identifier
            
        Returns:
            Analysis data or None if not found
        """
        cached = self._memory_analyses.get(trailer_id)
        if cached:
            logger.info(f"✅ Retrieved analysis for trailer (memory cache): {trailer_id}")
            return cached

        if not self.db and not self.firestore_db:
            logger.warning(f"⚠️ No analysis found for trailer (memory mode): {trailer_id}")
            return None

        try:
            if self.db:
                result = self.db.reference(f'analyses/{trailer_id}').get().val()
            else:
                snapshot = self.firestore_db.collection('analyses').document(trailer_id).get()
                result = snapshot.to_dict() if snapshot.exists else None

            if result:
                self._memory_analyses[trailer_id] = result
                logger.info(f"✅ Retrieved analysis for trailer: {trailer_id}")
                return result
            else:
                logger.warning(f"⚠️ No analysis found for trailer: {trailer_id}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Error retrieving from Firebase: {str(e)}")
            return None
    
    def save_comment(self, comment_data: Dict) -> bool:
        """
        Save individual comment
        
        Args:
            comment_data: Comment with metadata
            
        Returns:
            True if successful
        """
        comment_data['timestamp'] = datetime.now().isoformat()

        if not self.db and not self.firestore_db:
            self._memory_comments.append(comment_data)
            return True

        try:
            if self.db:
                self.db.reference('comments').push(comment_data)
            else:
                self.firestore_db.collection('comments').add(comment_data)
            return True
        except Exception as e:
            logger.error(f"❌ Error saving comment: {str(e)}")
            return False
    
    def get_all_analyses(self) -> List[Dict]:
        """Get all analyses from Firebase"""
        memory_items = list(self._memory_analyses.values())
        if not self.db and not self.firestore_db:
            return memory_items

        try:
            remote_items: List[Dict] = []
            if self.db:
                analyses = self.db.reference('analyses').get().val()
                if analyses:
                    remote_items = list(analyses.values())
            else:
                docs = self.firestore_db.collection('analyses').stream(timeout=5)
                remote_items = [doc.to_dict() for doc in docs]

            merged: Dict[str, Dict] = {}
            for item in remote_items + memory_items:
                if not isinstance(item, dict):
                    continue
                key = item.get('trailer_id') or item.get('id') or item.get('trailerId')
                if key:
                    merged[str(key)] = item
            if merged:
                return list(merged.values())
            return memory_items
        except Exception as e:
            logger.error(f"❌ Error retrieving analyses from Firebase, serving memory fallback: {str(e)}")
            return memory_items
    
    def get_recent_analyses(self, limit: int = 5) -> List[Dict]:
        """Get the most recently saved analyses, newest first.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of analysis records sorted by timestamp descending
        """
        analyses = self.get_all_analyses()
        analyses.sort(key=lambda item: item.get('timestamp', ''), reverse=True)
        return analyses[:limit]

    def delete_analysis(self, trailer_id: str) -> bool:
        """Delete analysis result"""
        if not self.db and not self.firestore_db:
            return self._memory_analyses.pop(trailer_id, None) is not None

        try:
            if self.db:
                self.db.reference(f'analyses/{trailer_id}').delete()
            else:
                self.firestore_db.collection('analyses').document(trailer_id).delete()
            logger.info(f"✅ Deleted analysis: {trailer_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting: {str(e)}")
            return False
    
    def health_check(self) -> bool:
        """Check Firebase connection health (memory mode always reports healthy)"""
        if not self.db and not self.firestore_db:
            return True

        try:
            payload = {'status': 'ok', 'timestamp': datetime.now().isoformat()}
            if self.db:
                self.db.reference('health').set(payload)
            else:
                self.firestore_db.collection('health').document('status').set(payload)
            logger.info("✅ Firebase health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Firebase health check failed: {str(e)}")
            return False
