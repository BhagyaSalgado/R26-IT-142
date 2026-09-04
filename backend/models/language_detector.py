"""Language Detection for Regional Analysis - Fixed English Keyword Collisions"""

from collections import Counter
from typing import List, Dict
import logging
import re

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detect comment language and map to estimated primary audience country with multi-script & Singlish support"""

    # Comprehensive mapping of ISO language codes & special tags to countries
    LANGUAGE_TO_COUNTRY = {
        'en': 'USA',
        'hi': 'India',
        'es': 'Mexico',
        'ta': 'Sri Lanka',
        'si': 'Sri Lanka',
        'singlish': 'Sri Lanka',  
        'sl': 'Sri Lanka',        
        'fr': 'France',
        'de': 'Germany',
        'pt': 'Brazil',
        'ja': 'Japan',
        'zh-cn': 'China',
        'zh-tw': 'China',
        'zh': 'China',
        'ar': 'Egypt',
        'ru': 'Russia',
        'ko': 'South Korea',
        'th': 'Thailand',
        'tr': 'Turkey',
        'te': 'India',
        'bn': 'India',
        'ml': 'India',
        'kn': 'India',
        'pa': 'India',
        'ne': 'Nepal',
        'my': 'Myanmar',
        'km': 'Cambodia',
        'lo': 'Laos',
        'vi': 'Vietnam',
        'id': 'Indonesia',
        'ms': 'Malaysia',
        'it': 'Italy',
        'fa': 'Iran',
        'ur': 'Pakistan',
    }

    # Unicode blocks for unique scripts that statistical detectors frequently misclassify
    SCRIPT_ONLY_LANGUAGES = [
        ('si', 0x0D80, 0x0DFF),  # Sinhala
        ('ta', 0x0B80, 0x0BFF),  # Tamil
        ('hi', 0x0900, 0x097F),  # Devanagari (Hindi/Nepali)
        ('bn', 0x0980, 0x09FF),  # Bengali
        ('te', 0x0C00, 0x0C7F),  # Telugu
        ('kn', 0x0C80, 0x0CFF),  # Kannada
        ('ml', 0x0D00, 0x0D7F),  # Malayalam
        ('pa', 0x0A00, 0x0A7F),  # Gurmukhi (Punjabi)
        ('th', 0x0E00, 0x0E7F),  # Thai
        ('lo', 0x0E80, 0x0EFF),  # Lao
        ('my', 0x1000, 0x109F),  # Myanmar (Burmese)
        ('km', 0x1780, 0x17FF),  # Khmer
        ('ar', 0x0600, 0x06FF),  # Arabic / Persian / Urdu
        ('ru', 0x0400, 0x04FF),  # Cyrillic (Russian / Ukrainian)
        ('ko', 0xAC00, 0xD7A3),  # Hangul (Korean)
        ('ja', 0x3040, 0x30FF),  # Hiragana/Katakana (Japanese)
        ('zh', 0x4E00, 0x9FFF),  # CJK Unified Ideographs (Chinese)
    ]

    # 🚀 FIXED: Removed generic words like 'film eka', 'trailer eka', 'eka', 'ane'
    SINGLISH_KEYWORDS = {
        'patta', 'sira', 'maru', 'ammo', 'fatta', 'pissu', 'aduwata', 
        'machan', 'machn', 'ado', 'audu', 'ape', 'meka', 'ela', 'elakiri', 
        'hodai', 'aul', 'ban', 'baba', 'yako', 'sdd', 'aiye', 'nangi','eka','ane',
        'akka', 'malli', 'amma', 'thaaththa', 'patta gathi', 'suwanda', 'niyamai'
    }

    # 🚀 FIXED: Removed 'he', 'hai', 'movie', 'tu', 'tum', 'aap', 'kya' which clash with English/common words
    HINGLISH_KEYWORDS = {
        'bhai', 'yaar', 'mast', 'jhakaas', 'bahut', 'achha', 'acha',
        'badiya','gazab', 'sahi hai', 'kadak', 'dekho', 'milega', 'bahut',
        'nehi', 'nahi', 'laga', 'bokbas', 'bakwas', 'pora', 'pura', 'yer',
        'mera', 'mujhe', 'karo'
    }

    def __init__(self):
        try:
            from langdetect import detect, DetectorFactory
            DetectorFactory.seed = 0
            self.detect = detect
            self.langdetect_available = True
        except ImportError:
            logger.warning("langdetect not available, relying entirely on script & keyword rules")
            self.langdetect_available = False

    def _detect_slang_language(self, text: str) -> str:
        """Detect Singlish or Hinglish based on specific regional slang words"""
        if not text:
            return ''
        
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        # Check Singlish intersection
        singlish_matches = words.intersection(self.SINGLISH_KEYWORDS)
        if len(singlish_matches) >= 1:
            return 'singlish'
            
        # Check Hinglish intersection
        hinglish_matches = words.intersection(self.HINGLISH_KEYWORDS)
        if len(hinglish_matches) >= 1:
            return 'hi'
            
        return ''

    def detect_language(self, text: str) -> str:
        """
        Detect ISO language code or custom region tag robustly
        """
        if not text or not isinstance(text, str):
            return 'en'

        # 1. 🔍 Strict Unicode Block Check (Catches Sinhala, Tamil, Russian, Arabic, Chinese, etc. instantly)
        for char in text:
            code = ord(char)
            for lang_code, start, end in self.SCRIPT_ONLY_LANGUAGES:
                if start <= code <= end:
                    return lang_code

        # 2. 🇱🇰/🇮🇳 Check for Romanized regional slangs (Singlish & Hinglish)
        slang_lang = self._detect_slang_language(text)
        if slang_lang:
            return slang_lang

        # 3. 🌐 Use statistical detector (langdetect) for standard European/global languages
        if self.langdetect_available:
            try:
                lang = self.detect(text)
                # Map similar variants if needed
                if lang in ['zh-cn', 'zh-tw']:
                    return 'zh'
                if lang in ['sl', 'tl']: 
                    return 'singlish'
                return lang
            except Exception:
                return 'en'
        
        return 'en'

    def detect_country(self, text: str) -> str:
        """
        Estimate audience country for a single comment text
        """
        lang = self.detect_language(text)
        return self.LANGUAGE_TO_COUNTRY.get(lang, 'USA')

    def get_regional_distribution(self, comments: List[str]) -> List[Dict]:
        """
        Analyze regional distribution from comment languages with accurate percentage calculation
        """
        if not comments:
            return []

        countries = [self.detect_country(comment) for comment in comments]
        country_counts = Counter(countries)
        total = len(comments)

        regional_distribution = [
            {
                'region': country,
                'value': round((count / total) * 100, 1),
                'count': count
            }
            for country, count in sorted(
                country_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]

        return regional_distribution