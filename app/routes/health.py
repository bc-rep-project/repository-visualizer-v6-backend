from flask import Blueprint, jsonify, request

health_bp = Blueprint('health', __name__, url_prefix='/api/health')
root_bp = Blueprint('root', __name__)

@health_bp.route('', methods=['GET'])
@health_bp.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Service is running'
    }), 200

@health_bp.route('/cors-test', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def cors_test():
    """
    Test endpoint for CORS validation. 
    
    Accepts all types of HTTP methods to test CORS pre-flight and actual requests.
    """
    method = request.method
    headers = dict(request.headers)
    # Filter out sensitive headers
    safe_headers = {k: v for k, v in headers.items() if k.lower() not in ['authorization', 'cookie']}
    
    return jsonify({
        'status': 'success',
        'message': 'CORS test successful',
        'method': method,
        'received_headers': safe_headers,
        'received_data': request.get_json() if request.is_json else None
    }), 200

@health_bp.route('/system', methods=['GET'])
def system_health():
    return jsonify({
        'status': 'healthy',
        'services': {
            'database': 'connected',
            'redis': 'connected'
        },
        'version': '1.0.0'
    }), 200

# Add a root endpoint
@root_bp.route('/', methods=['GET'])
def root():
    return jsonify({
        'status': 'healthy',
        'message': 'Repository Visualizer API is running',
        'version': '1.0.0',
        'documentation': '/api/docs'
    }), 200 