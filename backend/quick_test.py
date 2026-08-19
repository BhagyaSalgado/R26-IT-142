"""
Quick Test - Run this after setup to verify everything works
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test if all required imports work"""
    logger.info("Testing imports...")
    
    try:
        import flask
        logger.info("✅ Flask")
    except ImportError:
        logger.error("❌ Flask not found")
        return False
    
    try:
        import transformers
        logger.info("✅ Transformers (BERT)")
    except ImportError:
        logger.error("❌ Transformers not found")
        return False
    
    try:
        import firebase_admin
        logger.info("✅ Firebase Admin")
    except ImportError:
        logger.error("❌ Firebase Admin not found")
        return False
    
    try:
        import nltk
        logger.info("✅ NLTK")
    except ImportError:
        logger.error("❌ NLTK not found")
        return False
    
    try:
        import pandas
        logger.info("✅ Pandas")
    except ImportError:
        logger.error("❌ Pandas not found")
        return False
    
    return True


def test_config():
    """Test if configuration loads"""
    logger.info("\nTesting configuration...")
    
    try:
        from config.settings import DEBUG, FLASK_ENV, PRIMARY_MODEL
        logger.info(f"✅ Config loaded (ENV: {FLASK_ENV}, Debug: {DEBUG}, Model: {PRIMARY_MODEL})")
        return True
    except Exception as e:
        logger.error(f"❌ Config error: {e}")
        return False


def test_models():
    """Test if models can initialize"""
    logger.info("\nTesting model initialization...")
    
    try:
        from models.sentiment_model import SentimentAnalyzer
        logger.info("✅ Creating sentiment analyzer...")
        analyzer = SentimentAnalyzer()
        logger.info(f"✅ Sentiment analyzer ready (Model: {analyzer.current_model_name})")
        return True
    except Exception as e:
        logger.error(f"❌ Model initialization error: {e}")
        return False


def test_sentiment_prediction():
    """Test sentiment prediction"""
    logger.info("\nTesting sentiment prediction...")
    
    try:
        from models.sentiment_model import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        
        test_text = "This movie is absolutely fantastic!"
        result = analyzer.predict(test_text)
        
        logger.info(f"✅ Test text: '{test_text}'")
        logger.info(f"✅ Prediction: {result['label']} (confidence: {result['score']:.2f})")
        logger.info(f"✅ Model used: {result['model_used']}")
        return True
    except Exception as e:
        logger.error(f"❌ Prediction error: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("QUICK TEST - Sentiment Analysis Backend")
    logger.info("="*60 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Models", test_models),
        ("Prediction", test_sentiment_prediction),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test failed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("="*60)
    logger.info(f"Result: {passed}/{total} tests passed")
    logger.info("="*60 + "\n")
    
    if passed == total:
        logger.info("🎉 All tests passed! Backend is ready to run.")
        logger.info("\nStart the backend with: python app.py")
        return 0
    else:
        logger.error(f"⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
