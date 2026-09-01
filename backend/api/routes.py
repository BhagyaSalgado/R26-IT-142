"""API Routes for Sentiment Analysis"""

from datetime import datetime
import json
import logging
import subprocess
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import ProxyHandler, Request, build_opener, urlopen
from flask import Blueprint, request, jsonify
from services.sentiment_service import SentimentService
from services.firebase_service import FirebaseService
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


def _fetch_youtube_comments(video_id: str, max_comments: int = 1000) -> list:
    """Fetch top-level YouTube comments using YouTube Data API v3 REST."""
    comments = []
    if not YOUTUBE_API_KEY:
        raise RuntimeError('YOUTUBE_API_KEY not configured')

    def _request_comment_page(page_token: str | None) -> dict:
        query = {
            'part': 'snippet',
            'videoId': video_id,
            'maxResults': min(100, limit - fetched),
            'textFormat': 'plainText',
            'key': YOUTUBE_API_KEY
        }
        if page_token:
            query['pageToken'] = page_token

        url = f"https://www.googleapis.com/youtube/v3/commentThreads?{urlencode(query)}"
        request_obj = Request(
            url,
            method='GET',
            headers={'Accept': 'application/json'}
        )

        # Some Windows setups expose a blocked local proxy via env vars,
        # which causes [WinError 10013]. Retry once with proxies disabled.
        try:
            with urlopen(request_obj, timeout=15) as response:
                return json.loads(response.read().decode('utf-8'))
        except OSError as error:
            if getattr(error, 'winerror', None) == 10013:
                try:
                    opener = build_opener(ProxyHandler({}))
                    with opener.open(request_obj, timeout=15) as response:
                        return json.loads(response.read().decode('utf-8'))
                except OSError as proxyless_error:
                    if getattr(proxyless_error, 'winerror', None) != 10013:
                        raise
                    # Final fallback: call curl executable directly. In some
                    # Windows setups, outbound sockets are blocked for Python
                    # but allowed for curl.
                    cmd = [
                        'curl',
                        '--silent',
                        '--show-error',
                        '--fail',
                        '--max-time',
                        '20',
                        '--noproxy',
                        '*',
                        url
                    ]
                    try:
                        completed = subprocess.run(
                            cmd,
                            check=True,
                            capture_output=True,
                            text=True
                        )
                    except FileNotFoundError as missing_curl:
                        raise RuntimeError(
                            'Network blocked for Python (WinError 10013) and curl is not available'
                        ) from missing_curl
                    except subprocess.CalledProcessError as curl_error:
                        stderr = (curl_error.stderr or '').strip()
                        if stderr:
                            raise RuntimeError(
                                f'YouTube API request failed via curl: {stderr}'
                            ) from curl_error
                        raise RuntimeError(
                            'YouTube API request failed via curl'
                        ) from curl_error

                    return json.loads(completed.stdout)
            raise

    try:
        next_token = None
        fetched = 0
        limit = int(YOUTUBE_MAX_COMMENTS or max_comments)

        while fetched < limit:
            resp = _request_comment_page(next_token)
            error = resp.get('error', {})
            if error:
                message = error.get('message') or 'Unknown YouTube API error'
                raise RuntimeError(message)

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
    except HTTPError as e:
        detail = ''
        try:
            payload = json.loads(e.read().decode('utf-8'))
            detail = payload.get('error', {}).get('message', '')
        except Exception:
            detail = ''
        if detail:
            raise RuntimeError(f"YouTube API error {e.code}: {detail}") from e
        raise RuntimeError(f"YouTube API request failed with status {e.code}") from e
    except URLError as e:
        raise RuntimeError(f"YouTube API network error: {e.reason}") from e
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
        
        trailer_title = data.get('trailer_title') or data.get('trailerTitle', '')

        # Analyze comments
        analysis = sentiment_service.analyze_comments(comments)
        
        # Save to Firebase
        firebase_service.save_analysis_result(trailer_id, analysis, trailer_title)
        
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
            comments = _fetch_youtube_comments(video_id, max_comments=int(YOUTUBE_MAX_COMMENTS or 1000))
        except RuntimeError as re:
            return jsonify({'error': str(re), 'success': False}), 502
        except Exception as e:
            logger.error(f"Failed to fetch comments: {e}")
            return jsonify({'error': f'Failed to fetch comments: {e}', 'success': False}), 500

        if not comments:
            return jsonify({'error': 'No comments found for this video', 'success': False}), 404

        analysis = sentiment_service.analyze_comments(comments)

        # Save to Firebase using video_id as trailer_id
        firebase_service.save_analysis_result(video_id, analysis, trailer_title)

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


@api_bp.route('/history', methods=['GET'])
def get_history():
    """Get the most recently analyzed trailers (default: 5)."""
    try:
        limit = request.args.get('limit', default=5, type=int)
        limit = max(1, min(limit, 50))

        records = firebase_service.get_recent_analyses(limit)

        return jsonify({
            'success': True,
            'data': records,
            'count': len(records)
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
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
            'firebase_mode': firebase_service.mode,
            'model': model_info,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500
