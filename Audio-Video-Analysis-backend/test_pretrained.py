import sys
import os
import glob

# Ensure we can import from app
sys.path.insert(0, os.path.abspath("."))

from app.ml.model_loader import model_manager
from app.ml.trailer_analyzer import TrailerAnalyzer

def test_pretrained():
    print("Testing Pretrained Zero-Shot Classifier...")
    # Find the Batman trailer in storage/uploads
    batman_files = glob.glob("storage/uploads/Batman_ Knightfall*.mp4")
    if not batman_files:
        print("Batman Knightfall trailer not found!")
        return

    batman_file = batman_files[0]
    print(f"Found trailer: {batman_file}")

    # Load models
    print("Loading models (this will download HF weights on first run)...")
    analyzer = TrailerAnalyzer(model_manager)
    
    # Run analysis
    print("Running analysis...")
    results = analyzer.analyze(batman_file)
    
    print("\n--- Analysis Complete ---")
    print(f"Dominant Genre: {results.get('dominant_genre')}")
    print("\nSample Scene Typings (Pretrained Model Output):")
    final_output = results.get("final_system_output", [])
    
    # Print out a few scenes with high confidence
    for scene in final_output[:5]:
        print(f"Scene {scene['scene']} ({scene['time']}):")
        print(f"  Face: {scene.get('face_emotion')}, Audio: {scene.get('audio_emotion')}, Motion: {scene.get('M')}")
        print(f"  Objects: {scene.get('objects')}")
        print(f"  Predicted Type: {scene.get('scene_type')} (Conf: {scene.get('scene_type_confidence')})")

if __name__ == "__main__":
    test_pretrained()
