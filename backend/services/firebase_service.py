"""Firebase Database Service"""

import logging
import os
import firebase_admin
from firebase_admin import credentials, db, storage
from config.settings import FIREBASE_CREDENTIALS, FIREBASE_DATABASE_URL
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FirebaseService:
    """Firebase database operations"""
    
    def __init__(self):
        self.app = None
        self.db = None
        self.initialize_firebase()
    
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
                self.app = firebase_admin.initialize_app(
                    cred,
                    {'databaseURL': FIREBASE_DATABASE_URL}
                )
                logger.info("✅ Firebase initialized successfully")
            
            self.db = db
        except Exception as e:
            logger.warning(f"⚠️  Firebase initialization failed: {str(e)}")
            logger.warning("⚠️  Backend will work without Firebase")
            self.db = None
    
    def save_analysis_result(self, trailer_id: str, analysis_data: Dict) -> bool:
        """
        Save sentiment analysis result to Firebase
        
        Args:
            trailer_id: Unique trailer identifier
            analysis_data: Analysis results
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            logger.warning("Firebase not configured, skipping save")
            return False
            
        try:
            result_data = {
                **analysis_data,
                'trailer_id': trailer_id,
                'timestamp': datetime.now().isoformat(),
                'saved': True
            }
            
            # Save to Firebase
            self.db.reference(f'analyses/{trailer_id}').set(result_data)
            logger.info(f"✅ Saved analysis for trailer: {trailer_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error saving to Firebase: {str(e)}")
            return False
    
    def get_analysis_result(self, trailer_id: str) -> Optional[Dict]:
        """
        Retrieve saved analysis result
        
        Args:
            trailer_id: Unique trailer identifier
            
        Returns:
            Analysis data or None if not found
        """
        try:
            result = self.db.reference(f'analyses/{trailer_id}').get().val()
            if result:
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
        try:
            comment_data['timestamp'] = datetime.now().isoformat()
            self.db.reference('comments').push(comment_data)
            return True
        except Exception as e:
            logger.error(f"❌ Error saving comment: {str(e)}")
            return False
    
    def get_all_analyses(self) -> List[Dict]:
        """Get all analyses from Firebase"""
        try:
            analyses = self.db.reference('analyses').get().val()
            if analyses:
                return list(analyses.values())
            return []
        except Exception as e:
            logger.error(f"❌ Error retrieving analyses: {str(e)}")
            return []
    
    def delete_analysis(self, trailer_id: str) -> bool:
        """Delete analysis result"""
        try:
            self.db.reference(f'analyses/{trailer_id}').delete()
            logger.info(f"✅ Deleted analysis: {trailer_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting: {str(e)}")
            return False
    
    def health_check(self) -> bool:
        """Check Firebase connection health"""
        if not self.db:
            return False
            
        try:
            self.db.reference('health').set({'status': 'ok', 'timestamp': datetime.now().isoformat()})
            logger.info("✅ Firebase health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Firebase health check failed: {str(e)}")
            return False
