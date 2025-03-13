from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__, url_prefix='/api/health')

@health_bp.route('', methods=['GET'])
@health_bp.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Service is running'
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
root_bp = Blueprint('root', __name__)

@root_bp.route('/', methods=['GET'])
def root():
    return jsonify({
        'status': 'healthy',
        'message': 'Repository Visualizer API is running',
        'version': '1.0.0',
        'documentation': '/api/docs'
    }), 200 