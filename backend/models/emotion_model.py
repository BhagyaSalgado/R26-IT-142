"""Emotion Analysis Model with Fallback Chain (Enhanced Lexicon for Slang & Multilingual)"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    """Multi-emotion classifier with enhanced keyword fallback for global/local trailers"""

    LABEL_MAPPING = {
        'joy': 'Joy', 'happiness': 'Joy', 'love': 'Joy',
        'excitement': 'Excitement', 'anticipation': 'Excitement', 'optimism': 'Excitement',
        'anger': 'Anger', 'annoyance': 'Anger', 'disgust': 'Anger',
        'sadness': 'Sadness', 'disappointment': 'Sadness', 'grief': 'Sadness',
        'fear': 'Fear', 'anxiety': 'Fear',
        'surprise': 'Surprise', 'amazement': 'Surprise',
    }

    # 🚀 Expanded keywords including Singlish, internet slang, and emotive terms
    LEXICON_KEYWORDS = {
        'Joy': ['love', 'awesome', 'great', 'beautiful', 'best', 'happy', 'wonderful', 'amazing', 'patta', 'ela', 'sira', 'good', 'super', 'niyamai', 'fatta'],
        'Excitement': ['cant wait', 'excited', 'hype', 'insane', 'hyped', 'waiting', 'goosebumps', 'eager', 'masterpiece', 'pissu', 'maru', 'fire', 'supiri'],
        'Anger': ['worst', 'terrible', 'trash', 'hate', 'bad', 'horrible', 'ruined', 'disaster', 'waste', 'crap', 'flop', 'aul', 'pissu kathawak'],
        'Sadness': ['cry', 'cried', 'sad', 'heartbroken', 'miss', 'tears', 'disappointed', 'pain', 'lonely', 'emotional', 'paaduwa'],
        'Fear': ['scary', 'scared', 'creepy', 'terrified', 'fear', 'dark', 'horror', 'nightmare', 'spooky', 'chills'],
        'Surprise': ['omg', 'wow', 'unbelievable', 'shocked', 'unexpected', 'wtf', 'surprise', 'crazy', 'insane', 'plot twist', 'ammo', 'appata siri'],
    }

    def __init__(self):
        self.model = None
        self.current_model_name = None
        self.initialize_model()

    def initialize_model(self):
        models_to_try = [
            ('DistilRoBERTa-Emotion', 'j-hartmann/emotion-english-distilroberta-base'),
        ]

        for model_name, hf_path in models_to_try:
            try:
                from transformers import pipeline
                self.model = pipeline(
                    "text-classification",
                    model=hf_path,
                    top_k=None,
                    device=-1
                )
                self.current_model_name = model_name
                logger.info(f"✅ Loaded Emotion Model ({model_name}) successfully")
                return
            except Exception as e:
                logger.warning(f"❌ Emotion Model ({model_name}) failed to load: {str(e)}")

        self.current_model_name = 'Rule-based Lexicon'
        logger.info("ℹ️ Using Rule-based Lexicon Emotion Classifier fallback")

    def predict(self, text: str) -> Dict:
        if not text or not isinstance(text, str):
            return {'label': 'Joy', 'score': 0.5, 'model_used': 'Default'}

        text_lower = text.lower()

        if self.model:
            try:
                outputs = self.model(text)
                scores = outputs[0] if isinstance(outputs[0], list) else outputs
                top_pred = max(scores, key=lambda x: x['score'])
                raw_label = top_pred['label'].lower()
                mapped_label = self.LABEL_MAPPING.get(raw_label, 'Joy')

                return {
                    'label': mapped_label,
                    'score': round(float(top_pred['score']), 3),
                    'model_used': self.current_model_name
                }
            except Exception as e:
                logger.error(f"Emotion prediction error with model: {e}")

        # Fallback: Rule-based keyword count
        scores_map = {emotion: 0 for emotion in self.LEXICON_KEYWORDS.keys()}
        for emotion, keywords in self.LEXICON_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    scores_map[emotion] += 1

        top_emotion = max(scores_map.items(), key=lambda x: x[1])
        assigned_label = 'Joy' if top_emotion[1] == 0 else top_emotion[0]

        return {
            'label': assigned_label,
            'score': 0.75,
            'model_used': 'Rule-based Lexicon'
        }

    def batch_predict(self, texts: List[str]) -> List[Dict]:
        return [self.predict(text) for text in texts]