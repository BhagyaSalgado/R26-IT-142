import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.ml.model_loader import model_manager
from app.ml.trailer_analyzer import TrailerAnalyzer

def test_conjuring():
    print("Testing Universal Genre Classifier on The Conjuring...")
    # Find the Conjuring trailer
    target_file = "storage/uploads/The Conjuring - Official Main Trailer [HD]_9883089c.mp4"
    if not os.path.exists(target_file):
        print(f"File not found: {target_file}")
        return

    print("Loading models...")
    analyzer = TrailerAnalyzer(model_manager)
    
    print("Running analysis...")
    results = analyzer.analyze(target_file)
    
    print("\n--- Analysis Complete ---")
    print(f"Dominant Genre: {results.get('dominant_genre')}")
    print(f"Secondary Genre: {results.get('secondary_genre')}")
    
    print("\nFull Genre Mixture:")
    for genre, score in results.get("genre_mixture", {}).items():
        print(f"  {genre}: {score:.2%}")

if __name__ == "__main__":
    test_conjuring()
