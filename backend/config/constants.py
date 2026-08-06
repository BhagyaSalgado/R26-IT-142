"""Constants for the sentiment analysis application"""

# Sentiment Labels
SENTIMENT_LABELS = {
    'positive': 'POSITIVE',
    'neg': 'NEGATIVE',
    'neutral': 'NEUTRAL',
    'POSITIVE': 'POSITIVE',
    'NEGATIVE': 'NEGATIVE',
    'NEUTRAL': 'NEUTRAL',
}

# Emotion Types (6 Core Deeper Emotions)
EMOTION_TYPES = {
    'joy': 'Joy',
    'excitement': 'Excitement',
    'anger': 'Anger',
    'sadness': 'Sadness',
    'fear': 'Fear',
    'surprise': 'Surprise',
}

# Supported Languages & Primary Country Estimates
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'es': 'Spanish',
    'ta': 'Tamil',
    'fr': 'French',
    'de': 'German',
    'pt': 'Portuguese',
    'ja': 'Japanese',
    'zh': 'Chinese',
    'ko': 'Korean',
    'ar': 'Arabic',
    'ru': 'Russian',
}

# Movie Trailer Topic Keywords for Extraction
TOPIC_KEYWORDS = {
    'Storyline': ['story', 'plot', 'concept', 'climax', 'twist', 'script', 'narrative', 'storyline', 'ending'],
    'Actors': ['actor', 'actress', 'hero', 'heroine', 'cast', 'acting', 'performance', 'role', 'character', 'star'],
    'Music': ['music', 'song', 'bgm', 'soundtrack', 'theme', 'score', 'audio', 'sound', 'beats'],
    'Visual Effects': ['cgi', 'vfx', 'visuals', 'graphics', 'effects', 'animation', 'cinematography', 'shots', '3d'],
    'Quality': ['goosebumps', 'masterpiece', 'blockbuster', 'hype', 'trailer', 'teaser', 'direction', 'quality', 'editing'],
}

# API Response Templates
RESPONSE_TEMPLATE = {
    'success': True,
    'data': None,
    'error': None,
    'timestamp': None,
    'model_used': None,
}

# Error Messages
ERROR_MESSAGES = {
    'INVALID_URL': 'Invalid trailer URL provided',
    'MODEL_LOAD_FAILED': 'Failed to load sentiment model',
    'PREDICTION_FAILED': 'Sentiment prediction failed',
    'NO_COMMENTS': 'No comments found for the trailer',
    'DATABASE_ERROR': 'Database operation failed',
}

# Success Messages
SUCCESS_MESSAGES = {
    'ANALYSIS_COMPLETE': 'Sentiment analysis completed successfully',
    'TRAINING_COMPLETE': 'Model training completed successfully',
    'PREDICTION_SUCCESS': 'Sentiment prediction successful',
}
