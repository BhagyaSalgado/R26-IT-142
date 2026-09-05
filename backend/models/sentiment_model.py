import logging
import os
import re
from typing import Dict
from config.settings import MODEL_PATH

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Robust Sentiment Analyzer using Custom XLM-RoBERTa + Multilingual Slang/Emoji Lexicon"""
    
    def __init__(self):
        self.model = None
        self.current_model_name = None
        
        # 🚀 Supercharged Lexicon for Singlish, Hinglish, Sinhala, Tamil, Global & Emojis
        self.positive_keywords = [
            # Singlish
            'patta', 'sira', 'maru', 'supiri', 'ela', 'elakiri', 'niyamai', 'hodai', 'adarei', 'fatta', 'ammo', 'ammor', 'uparima',
            # Hinglish
            'mast', 'jhakaas', 'badiya', 'superb', 'gazab', 'kadak', 'acha', 'zabardast', 'ek no', 'ek number',
            # Sinhala & Tamil
            'සුපිරි', 'පට්ට', 'නියමයි', 'හොඳයි', 'ආදරෙයි', 'එළ', 'මරු', 'சூப்பர்', 'அருமை', 'நல்ல',
            # Global
            'awesome', 'great', 'best', 'love', 'excellent', 'masterpiece', 'amazing', 'good', 'beautiful',
            # Emojis
            '❤️', '🔥', '😍', '👍', '🎉', '✨', '🥹', '👏', '🙌', '💯', '🥰'
        ]
        
        self.negative_keywords = [
            # Singlish
            'aul', 'chaater', 'chater', 'gu', 'wadak na', 'melo rahak na', 'gok', 'epa', 'jarawa', 'pacha', 'boruwak', 'pissu',
            # Hinglish
            'bakwas', 'bokbas', 'bekar', 'ghatiya', 'kachra', 'tatti', 'bura', 'flop', 'nehi', 'nahi', 'kharab',
            # Sinhala & Tamil
            'අවුල්', 'චාටර්', 'වැඩක් නෑ', 'ගූ', 'මෙලෝ රහක් නෑ', 'ජරාව', 'ගොක්', 'එපා', 'மோசம்', 'கேவலம்', 'குப்பை',
            # Global
            'worst', 'terrible', 'bad', 'hate', 'awful', 'trash', 'boring', 'flop', 'disaster', 'crap',
            # Emojis
            '🤮', '💩', '👎', '😡', '🤬', '💀', '🗑️', '📉', '🤢'
        ]
        
        self.initialize_model()
    
    def initialize_model(self):
        from transformers import pipeline
        
        # --- Plan A: Custom fine-tuned XLM-RoBERTa ---
        if os.path.exists(MODEL_PATH) and os.path.exists(os.path.join(MODEL_PATH, 'config.json')):
            try:
                self.model = pipeline(
                    "sentiment-analysis",
                    model=MODEL_PATH,
                    tokenizer=MODEL_PATH,
                    device=-1  
                )
                self.current_model_name = "Custom-XLM-RoBERTa"
                logger.info(f"✅ Loaded Custom Colab Model successfully from {MODEL_PATH}")
                return
            except Exception as e:
                logger.warning(f"⚠️ Failed to load custom model from {MODEL_PATH}: {str(e)}")
        
        # --- Plan B: Multilingual Fallback ---(BERT)
        fallback_model = "nlptown/bert-base-multilingual-uncased-sentiment"
        try:
            logger.info(f"🔄 Attempting to load multilingual fallback model...")
            self.model = pipeline(
                "sentiment-analysis",
                model=fallback_model,
                tokenizer=fallback_model,
                device=-1
            )
            self.current_model_name = "Fallback-Multilingual-BERT"
            logger.info(f"✅ Loaded Fallback Multilingual Model successfully")
        except Exception as e:
            logger.critical(f"❌ All model initialization failed: {str(e)}")
            self.model = None
            self.current_model_name = "Failed"

    def _check_lexicon(self, text: str) -> str:
        """Check text against the slang & emoji lexicon"""
        text_lower = text.lower()
        
        # Count positive and negative matches
        pos_count = sum(1 for word in self.positive_keywords if word in text_lower)
        neg_count = sum(1 for word in self.negative_keywords if word in text_lower)
        
        if pos_count > neg_count:
            return 'POSITIVE'
        elif neg_count > pos_count:
            return 'NEGATIVE'
        return 'NEUTRAL'

    def predict(self, text: str) -> Dict:
        if not text or not isinstance(text, str):
            return {'label': 'NEUTRAL', 'score': 0.5, 'model_used': self.current_model_name or 'None'}
        
        # 1. Get Lexicon Prediction (Great for Slang & Emojis)
        lexicon_label = self._check_lexicon(text)
        
        # 2. Get ML Model Prediction
        ml_label = 'NEUTRAL'
        ml_score = 0.5
        
        if self.model:
            try:
                result = self.model(text)
                raw_label = str(result[0]['label']).upper()
                ml_score = float(result[0]['score'])
                
                if raw_label in ['POSITIVE', 'LABEL_2', '5 STARS', '4 STARS', 'POS']:
                    ml_label = 'POSITIVE'
                elif raw_label in ['NEGATIVE', 'LABEL_0', '1 STAR', '2 STARS', 'NEG']:
                    ml_label = 'NEGATIVE'
                else:
                    ml_label = 'NEUTRAL'
            except Exception as e:
                logger.error(f"Prediction error: {str(e)}")
        
        # 3. 🚀 Smart Decision Making (Merge ML and Lexicon)
        final_label = ml_label
        final_score = ml_score
        model_used = self.current_model_name

        # If the ML model is confused/neutral but the Lexicon clearly sees slang/emojis (e.g. "patta", "🔥")
        if ml_label == 'NEUTRAL' and lexicon_label != 'NEUTRAL':
            final_label = lexicon_label
            final_score = 0.85  # Boost confidence since we caught a strong keyword
            model_used = f"{self.current_model_name} + Lexicon"
            
        # Or if the ML model entirely failed, trust the Lexicon
        elif not self.model:
            final_label = lexicon_label
            final_score = 0.75
            model_used = 'Multilingual Lexicon'

        return {
            'label': final_label,
            'score': final_score,
            'model_used': model_used
        }

    def batch_predict(self, texts: list) -> list:
        """Predict sentiment for multiple texts efficiently"""
        results = []
        for text in texts:
            try:
                results.append(self.predict(text))
            except Exception as e:
                logger.error(f"Batch prediction error: {str(e)}")
                results.append({
                    'label': 'NEUTRAL',
                    'score': 0.5,
                    'model_used': 'Error'
                })
        return results

    def get_model_info(self) -> Dict:
        """Get current model status and information"""
        return {
            'current_model': self.current_model_name,
            'model_source': MODEL_PATH,
            'using_custom_model': self.current_model_name == "Custom-XLM-RoBERTa",
            'status': 'Ready' if self.model else 'Failed'
        }