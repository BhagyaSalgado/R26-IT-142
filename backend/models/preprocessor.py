import re
import logging
import unicodedata
from typing import List

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """Preprocess text safely for XLM-RoBERTa without breaking sentence structure"""
    
    def clean_text(self, text: str) -> str:
        # Remove URLs and Emails
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\S+@\S+', '', text)
        
        # Keep letters/marks/numbers safely for Multilingual text (Sinhala/Tamil etc)
        allowed_punctuation = set(' ?!.,')
        text = ''.join(
            ch for ch in text
            if unicodedata.category(ch)[0] in ('L', 'M', 'N') or ch in allowed_punctuation
        )
        
        # Remove extra whitespace
        return re.sub(r'\s+', ' ', text).strip()
    
    def handle_emoji(self, text: str) -> str:
        emoji_dict = {
            # Positive & Joy
            '😀': 'happy', '😁': 'grinning', '😂': 'funny', '🤣': 'hilarious',
            '😃': 'joy', '😄': 'happy', '😅': 'relief', '😆': 'laugh',
            '😊': 'smiling', '😇': 'angel', '🙂': 'nice', '😉': 'winks',
            
            # Love & Support
            '😍': 'love', '🥰': 'adore', '😘': 'kiss', '❤️': 'love', 
            '💖': 'heart', '💙': 'love', '💚': 'love', '💛': 'love', 
            '💜': 'love', '🖤': 'love', '💯': 'perfect', '✨': 'magical',
            
            # Hype & Energy  
            '🔥': 'fire', '💥': 'explosive', '⚡': 'epic', '⭐': 'star',
            '🌟': 'brilliant', '🚀': 'masterpiece', '👏': 'applause', 
            '🙌': 'celebration', '💪': 'strong', '👊': 'awesome',
            
            # Negative & Anger
            '😢': 'sad', '😭': 'crying', '😠': 'angry', '😡': 'furious',
            '🤬': 'cursing', '👎': 'bad', '💩': 'trash', '🤮': 'disgusted',
            '💀': 'dead', '☠️': 'terrible', '📉': 'flop',
            
            # Neutral / Reactions
            '👍': 'good', '🤔': 'thinking', '😮': 'surprised',
            '🤯': 'mindblown', '👀': 'watching', '🍿': 'popcorn'
        }
        
        for emoji, word in emoji_dict.items():
            text = text.replace(emoji, f' {word} ')
            
        return text
    
    def preprocess(self, text: str) -> str:
        """Lightweight preprocessing - Do NOT remove stopwords or lemmatize!"""
        text = self.handle_emoji(text)
        return self.clean_text(text)
    
    def batch_preprocess(self, texts: List[str]) -> List[str]:
        return [self.preprocess(text) for text in texts]