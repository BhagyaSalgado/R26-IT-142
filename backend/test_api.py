"""
API Client - Test backend endpoints
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"


class SentimentAPIClient:
    """Client for Sentiment Analysis API"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    def health_check(self):
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.base_url}/api/sentiment/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_comments(self, comments, trailer_id="test_123"):
        """Analyze multiple comments"""
        data = {
            "comments": comments,
            "trailer_id": trailer_id
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/sentiment/analyze",
                json=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_single(self, comment):
        """Analyze single comment"""
        data = {"comment": comment}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/sentiment/analyze-single",
                json=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_model_info(self):
        """Get model information"""
        try:
            response = requests.get(f"{self.base_url}/api/sentiment/model-info")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_status(self):
        """Get system status"""
        try:
            response = requests.get(f"{self.base_url}/api/sentiment/status")
            return response.json()
        except Exception as e:
            return {"error": str(e)}


def main():
    """Test API endpoints"""
    
    print("\n" + "="*60)
    print("SENTIMENT ANALYSIS API CLIENT")
    print("="*60 + "\n")
    
    client = SentimentAPIClient()
    
    # Test 1: Health check
    print("1️⃣  Testing health check...")
    result = client.health_check()
    print(json.dumps(result, indent=2))
    
    if "error" in result:
        print("\n❌ Backend is not running!")
        print("Start it with: python app.py")
        return 1
    
    # Test 2: Model info
    print("\n2️⃣  Getting model information...")
    result = client.get_model_info()
    print(json.dumps(result, indent=2))
    
    # Test 3: Single comment
    print("\n3️⃣  Analyzing single comment...")
    comment = "This movie trailer looks absolutely amazing! Can't wait!"
    result = client.analyze_single(comment)
    print(json.dumps(result, indent=2))
    
    # Test 4: Multiple comments
    print("\n4️⃣  Analyzing multiple comments...")
    comments = [
        "This is the best movie I've ever seen!",
        "Terrible, waste of time.",
        "It's okay, nothing special.",
        "The special effects are incredible!",
        "I hated it."
    ]
    result = client.analyze_comments(comments)
    print(json.dumps(result, indent=2))
    
    # Test 5: System status
    print("\n5️⃣  System status...")
    result = client.get_status()
    print(json.dumps(result, indent=2))
    
    print("\n" + "="*60)
    print("✅ API Test Complete!")
    print("="*60 + "\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
