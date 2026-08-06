"""API Routes for Sentiment Analysis"""

from flask import Blueprint, request, jsonify
from services.sentiment_service import SentimentService
from services.firebase_service import FirebaseService
from datetime import datetime
import logging
from config.settings import YOUTUBE_API_KEY, YOUTUBE_MAX_COMMENTS

logger = logging.getLogger(__name__)

# Initialize services
sentiment_service = SentimentService()
firebase_service = FirebaseService()

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/sentiment')


def _extract_video_id(url: str) -> str:
    """Extract YouTube video id from common URL formats."""
    if not url:
        return ''
    try:
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(url)
        hostname = (parsed.hostname or '').lower()
        if hostname in ('youtu.be', 'www.youtu.be'):
            return parsed.path.lstrip('/')
        if 'youtube' in hostname:
            qs = parse_qs(parsed.query)
            if 'v' in qs:
                return qs['v'][0]
    except Exception:
        return ''
    return ''


def _fetch_youtube_comments(video_id: str, max_comments: int = 200) -> list:
    """Fetch top-level YouTube comments using the Data API v3.

    Requires `YOUTUBE_API_KEY` to be set in config.settings.
    """
    comments = []
    if not YOUTUBE_API_KEY:
        raise RuntimeError('YOUTUBE_API_KEY not configured')

    try:
        from googleapiclient.discovery import build

        service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        next_token = None
        fetched = 0
        limit = int(YOUTUBE_MAX_COMMENTS or max_comments)

        while fetched < limit:
            resp = (
                service.commentThreads()
                .list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=min(100, limit - fetched),
                    pageToken=next_token,
                    textFormat='plainText',
                )
                .execute()
            )

            for item in resp.get('items', []):
                top = item.get('snippet', {}).get('topLevelComment', {}).get('snippet', {})
                text = top.get('textDisplay') or top.get('textOriginal')
                if text:
                    comments.append(text)
                    fetched += 1
                    if fetched >= limit:
                        break

            next_token = resp.get('nextPageToken')
            if not next_token:
                break

        return comments
    except Exception as e:
        logger.error(f"YouTube fetch error: {e}")
        raise


@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'model': sentiment_service.analyzer.current_model_name
    }), 200


@api_bp.route('/analyze', methods=['POST'])
def analyze():
    """Main sentiment analysis endpoint"""
    try:
        data = request.json
        
        if not data or 'comments' not in data:
            return jsonify({
                'error': 'No comments provided',
                'success': False
            }), 400
        
        comments = data.get('comments', [])
        trailer_id = data.get('trailer_id', 'unknown')
        
        if not isinstance(comments, list):
            return jsonify({
                'error': 'Comments must be a list',
                'success': False
            }), 400
        
        # Analyze comments
        analysis = sentiment_service.analyze_comments(comments)
        
        # Save to Firebase
        firebase_service.save_analysis_result(trailer_id, analysis)
        
        return jsonify({
            'success': True,
            'data': analysis,
            'trailer_id': trailer_id,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@api_bp.route('/analyze/from-url', methods=['POST'])
def analyze_from_url():
    """Fetch comments for a YouTube trailer URL and analyze them."""
    try:
        data = request.json or {}
        trailer_url = data.get('trailer_url') or data.get('trailerUrl')
        trailer_title = data.get('trailer_title') or data.get('trailerTitle', '')

        if not trailer_url:
            return jsonify({'error': 'No trailer_url provided', 'success': False}), 400

        video_id = _extract_video_id(trailer_url)
        if not video_id:
            return jsonify({'error': 'Could not extract video id from URL', 'success': False}), 400

        try:
            comments = _fetch_youtube_comments(video_id, max_comments=int(YOUTUBE_MAX_COMMENTS or 200))
        except RuntimeError as re:
            return jsonify({'error': str(re), 'success': False}), 500
        except Exception as e:
            logger.error(f"Failed to fetch comments: {e}")
            return jsonify({'error': 'Failed to fetch comments', 'success': False}), 500

        if not comments:
            return jsonify({'error': 'No comments found for this video', 'success': False}), 404

        analysis = sentiment_service.analyze_comments(comments)

        # Save to Firebase using video_id as trailer_id
        firebase_service.save_analysis_result(video_id, analysis)

        return jsonify({
            'success': True,
            'data': analysis,
            'trailer_id': video_id,
            'trailer_title': trailer_title,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error in analyze_from_url: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@api_bp.route('/analyze/<trailer_id>', methods=['GET'])
def get_analysis(trailer_id):
    """Get cached analysis result"""
    try:
        result = firebase_service.get_analysis_result(trailer_id)
        
        if result:
            return jsonify({
                'success': True,
                'data': result
            }), 200
        else:
            return jsonify({
                'error': 'Analysis not found',
                'success': False
            }), 404
    
    except Exception as e:
        logger.error(f"Error retrieving analysis: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@api_bp.route('/analyze-single', methods=['POST'])
def analyze_single():
    """Analyze single comment"""
    try:
        data = request.json
        comment = data.get('comment', '')
        
        if not comment:
            return jsonify({
                'error': 'No comment provided',
                'success': False
            }), 400
        
        result = sentiment_service.analyze_single_comment(comment)
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing single comment: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@api_bp.route('/model-info', methods=['GET'])
def model_info():
    """Get model information"""
    try:
        info = sentiment_service.get_service_info()
        return jsonify({
            'success': True,
            'data': info
        }), 200
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@api_bp.route('/status', methods=['GET'])
def status():
    """Get system status"""
    try:
        firebase_ok = firebase_service.health_check()
        model_info = sentiment_service.get_service_info()
        
        return jsonify({
            'success': True,
            'firebase': 'ok' if firebase_ok else 'error',
            'model': model_info['model_info'],
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500
