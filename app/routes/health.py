from flask import Blueprint, jsonify
from ..services.repository_service import RepositoryService

health_bp = Blueprint('health', __name__, url_prefix='/api/health')

@health_bp.route('/', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

@health_bp.route('/system', methods=['GET'])
def system_check():
    """Check system requirements."""
    git_available = RepositoryService.check_git_available()
    return jsonify({
        'status': 'healthy',
        'git_available': git_available,
    }), 200 if git_available else 500 