"""Main Flask Application - Comment Sentiment Analysis Backend"""

import logging
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from config.settings import DEBUG, CORS_ORIGINS, SECRET_KEY
from api.routes import api_bp
from utils.logger import setup_logger

# Setup logger
logger = setup_logger()

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = DEBUG

# Setup CORS - Allow all origins for development
CORS(app, 
     origins="*",
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=False)

# Register blueprints
app.register_blueprint(api_bp)


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Movie Trailer Comment Sentiment Analysis API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/sentiment/health',
            'analyze': '/api/sentiment/analyze',
            'analyze_single': '/api/sentiment/analyze-single',
            'model_info': '/api/sentiment/model-info',
            'status': '/api/sentiment/status'
        }
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'status': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'status': 500
    }), 500


@app.before_request
def before_request():
    """Before request hook"""
    logger.info(f"Request: {request.method} {request.path}")


@app.after_request
def after_request(response):
    """After request hook"""
    logger.info(f"Response: {response.status_code}")
    return response


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('./logs', exist_ok=True)
    os.makedirs('./data', exist_ok=True)
    os.makedirs('./models', exist_ok=True)
    
    logger.info("🚀 Starting Comment Sentiment Analysis Backend")
    logger.info(f"🔧 Environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"🐛 Debug: {DEBUG}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=DEBUG,
        threaded=True
    )
