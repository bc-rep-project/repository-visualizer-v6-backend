from flask import Blueprint, jsonify, request, current_app
import logging

test_bp = Blueprint('test', __name__, url_prefix='/api/test')

@test_bp.route('/cors', methods=['GET'])
def test_cors():
    """
    Test endpoint to verify CORS configuration
    """
    # Log CORS configuration
    logger = logging.getLogger('flask.app')
    logger.info("CORS_ORIGINS: %s", current_app.config.get('CORS_ORIGINS'))
    logger.info("Request Origin: %s", request.headers.get('Origin'))
    logger.info("Environment: %s", current_app.config.get('ENV'))
    
    # Return CORS configuration as JSON
    return jsonify({
        'message': 'CORS test successful',
        'cors_origins': current_app.config.get('CORS_ORIGINS'),
        'request_origin': request.headers.get('Origin'),
        'environment': current_app.config.get('ENV')
    }), 200 