"""Test full 4-stage Comment Sentiment & Emotion Analysis Pipeline"""

import sys
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_pipeline():
    logger.info("Initializing SentimentService...")
    from services.sentiment_service import SentimentService
    service = SentimentService()

    sample_comments = [
        "Amazing trailer! Can't wait to watch it. The storyline looks epic!",
        "Worst acting ever. Total waste of time and money.",
        "The background music and BGM is awesome! Pure goosebumps 🔥",
        "VFX high level-ah iruku, visuals overall super ah iruku bro",
        "Bahut hi badiya trailer hai, action scene zabardast hai!",
        "Average movie, nothing special about the CGI or plot.",
        "I cried watching the trailer, so emotional and tragic story.",
        "Scary dark atmosphere, terrified to watch this alone in theatre!",
        "OMG unexpected plot twist at the ending! OMG shocking!",
        "The cast and lead actor gave a brilliant performance."
    ]

    logger.info(f"Analyzing {len(sample_comments)} sample comments...")
    result = service.analyze_comments(sample_comments)

    print("\n" + "="*60)
    print("ANALYSIS RESULT SUMMARY")
    print("="*60)
    print(f"Total Comments Processed: {result['totalComments']}")
    print(f"Models Used: {result['modelUsed']}\n")

    print("1. Sentiment Distribution:")
    print(json.dumps(result['sentiment'], indent=2))

    print("\n2. Deeper Emotion Distribution:")
    print(json.dumps(result['deeperEmotions'], indent=2))

    print("\n3. Top Discussion Topics:")
    print(json.dumps(result['commentTopics'], indent=2))

    print("\n4. Estimated Country Distribution:")
    print(json.dumps(result['regionalInterest'], indent=2))

    print("\n5. Sample Per-Comment Output Table (First 3):")
    for item in result['detailedResults'][:3]:
        print(f"  Comment: '{item['text']}'")
        print(f"    -> Lang: {item['language']} | Country: {item['country']} | Sentiment: {item['sentiment']} | Emotion: {item['emotion']} | Topic: {item['topic']}")
        print("-" * 50)

    print("\nPipeline execution completed successfully!")

if __name__ == '__main__':
    test_pipeline()
