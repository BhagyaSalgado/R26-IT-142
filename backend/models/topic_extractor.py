"""Topic Extraction from Comments - Fully Multilingual & Global Support"""

from collections import Counter
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TopicExtractor:
    """Extract main discussion topics using a massive multilingual keyword dictionary"""
    
    def __init__(self):
        # 🚀 Supercharged Multilingual Topic Dictionary
        # Covers: English, Singlish, Hinglish, Sinhala, Tamil, Spanish, Russian, Arabic, Chinese
        self.topic_keywords = {
            'Music': [
                # English, Singlish, Hinglish
                'song', 'bgm', 'music', 'audio', 'soundtrack', 'voice', 'singing', 'ost', 'beats',
                'sindu', 'sinduwa', 'sangeetha', 'geetha', 'beat eka', 'sadda', 'voice eka',
                'gaana', 'gane', 'awaaz', 'sangeet', 'dhun', 'gaane',
                # Sinhala & Tamil Scripts
                'සින්දු', 'සංගීත', 'ගීත', 'නාද', 'හඬ', 'பாடல்', 'இசை', 'சத்தம்', 'பாட்டு',
                # Global (Spanish, Russian, Arabic, Chinese)
                'música', 'canción', 'sonido', 'музыка', 'песня', 'звук', 'موسيقى', 'أغنية', '音乐', '歌曲', '配乐'
            ],
            'Visual Effects': [
                # English, Singlish, Hinglish
                'vfx', 'cgi', 'gfx', 'visuals', 'graphics', 'animation', 'effects', 'quality', 'screen', 'action',
                'darsana', 'lassanai', 'edit eka', 'camera quality',
                'scene', 'editing', 'fight', 'action scene', 'visual',
                # Sinhala & Tamil Scripts
                'දර්ශන', 'රූප', 'සංස්කරණය', 'ක්‍රියාදාම', 'ග්‍රැෆික්', 'கிராபிக்ஸ்', 'காட்சிகள்', 'சண்டை',
                # Global
                'efectos', 'visuales', 'animación', 'acción', 'эффекты', 'графика', 'анимация', 'مؤثرات', 'بصرية', '特效', '视觉', '动画'
            ],
            'Actors': [
                # English, Singlish, Hinglish
                'acting', 'actor', 'actress', 'cast', 'performance', 'star', 'hero', 'villain', 'role', 'character', 'lead',
                'naluwa', 'niliya', 'nayakaya', 'ranganaya', 'acting patta', 'kolla', 'kella', 'charithaya',
                'heroine', 'bhai', 'kalakar', 'starcast', 'acting mast',
                # Sinhala & Tamil Scripts
                'නළුවා', 'නිළිය', 'රංගනය', 'චරිතය', 'වීරයා', 'නළු', 'நடிகர்', 'நடிகை', 'நடிப்பு', 'ஹீரோ',
                # Global
                'actuación', 'elenco', 'personaje', 'актер', 'актриса', 'игра', 'персонаж', 'ممثل', 'ممثلة', 'تمثيل', '演员', '演技', '角色'
            ],
            'Direction': [
                # English, Singlish, Hinglish
                'director', 'direction', 'screenplay', 'scene', 'shot', 'camera', 'cinematography', 'edit',
                'adyakshanaya', 'direction eka', 'cam eka', 'shot eka', 'director patta',
                'nirdeshan', 'direction acha',
                # Sinhala & Tamil Scripts
                'අධ්‍යක්ෂණය', 'අධ්‍යක්ෂක', 'කැමරා', 'තිර රචනය', 'இயக்குனர்', 'இயக்கம்', 'திரைக்கதை', 'கேமரா',
                # Global
                'dirección', 'guion', 'режиссер', 'режиссура', 'сценарий', 'مخرج', 'إخراج', 'سيناريو', '导演', '执导', '镜头', '剧本'
            ],
            'Storyline': [
                # English, Singlish, Hinglish
                'story', 'plot', 'script', 'twist', 'ending', 'beginning', 'concept', 'idea', 'tale',
                'kathawa', 'kathaawa', 'story eka', 'boruwak', 'therumak', 'anthima', 'katha',
                'kahani', 'suspense', 'script acha', 'kahaani', 'katha',
                # Sinhala & Tamil Scripts
                'කතාව', 'තේමාව', 'පිටපත', 'අවසානය', 'கதை', 'கிளைமாக்ஸ்', 'ஸ்கிரிப்ட்',
                # Global
                'historia', 'trama', 'final', 'история', 'сюжет', 'концовка', 'قصة', 'حبكة', 'نهاية', '故事', '剧情', '结局'
            ]
        }
    
    def extract_topic_for_comment(self, comment: str) -> str:
        if not comment or not isinstance(comment, str):
            return 'General'

        comment_lower = comment.lower()
        topic_scores = {topic: 0 for topic in self.topic_keywords.keys()}

        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword in comment_lower:
                    topic_scores[topic] += 1

        top_topic = max(topic_scores.items(), key=lambda x: x[1])
        # If at least one keyword is found, return that topic
        if top_topic[1] > 0:
            return top_topic[0]
            
        return 'Storyline'  # Default fallback if no keywords match

    def extract_topics(self, comments: List[str]) -> Dict[str, int]:
        topic_counts = {topic: 0 for topic in self.topic_keywords.keys()}
        
        for comment in comments:
            topic = self.extract_topic_for_comment(comment)
            if topic in topic_counts:
                topic_counts[topic] += 1
            else:
                topic_counts[topic] = 1
        
        return dict(sorted(
            topic_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ))
    
    def get_top_n_topics(self, comments: List[str], n: int = 5) -> List[Dict]:
        topics = self.extract_topics(comments)
        return [
            {'topic': topic, 'mentions': count}
            for topic, count in list(topics.items())[:n]
            if count > 0
        ]
    
    def analyze_topics(self, comments: List[str]) -> Dict:
        topics = self.extract_topics(comments)
        total_comments = len(comments)
        
        return {
            'topics': [
                {
                    'topic': topic,
                    'mentions': count,
                    'percentage': (count / total_comments * 100) if total_comments > 0 else 0
                }
                for topic, count in topics.items()
                if count > 0
            ],
            'total_topics_found': len([t for t, c in topics.items() if c > 0]),
            'top_topic': max(topics.items(), key=lambda x: x[1])[0] if max(topics.values()) > 0 else None
        }