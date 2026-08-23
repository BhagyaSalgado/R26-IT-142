"""Test Sentiment Analysis Service"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.sentiment_service import SentimentService


def test_sentiment_analysis():
    """Test sentiment analysis"""
    
    print("🧪 Testing Sentiment Analysis Service...\n")
    
    # Initialize service
    service = SentimentService()
    
    # Test comments
    test_comments = [
        "This movie trailer is absolutely amazing! I can't wait to watch it.",
        "The worst trailer I've ever seen. Total disappointment.",
        "It's okay, nothing special.",
        "WOW! The special effects are incredible!",
        "I hated every second of it.",
    ]
    
    print("📝 Test Comments:")
    for i, comment in enumerate(test_comments, 1):
        print(f"{i}. {comment}\n")
    
    # Analyze
    print("\n🔍 Analyzing comments...\n")
    result = service.analyze_comments(test_comments)
    
    # Display results
    print("✅ Analysis Results:")
    print(f"  Positive: {result['sentiment']['positive']}%")
    print(f"  Neutral: {result['sentiment']['neutral']}%")
    print(f"  Negative: {result['sentiment']['negative']}%")
    print(f"\n  Total Comments: {result['totalComments']}")
    print(f"  Model Used: {result['modelUsed']}")
    
    print(f"\n  Topics Found: {[t['topic'] for t in result['commentTopics']]}")
    print(f"\n  Regions:")
    for region in result['regionalInterest']:
        print(f"    - {region['region']}: {region['value']}%")
    
    print("\n✅ Test completed successfully!")


if __name__ == '__main__':
    test_sentiment_analysis()
