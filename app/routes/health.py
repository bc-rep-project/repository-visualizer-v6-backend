from flask import Blueprint, jsonify
from ..services.repository_service import RepositoryService

health_bp = Blueprint('health', __name__)

@health_bp.route('/')
def health_check():
    """Health check endpoint."""
    git_available = RepositoryService.check_git_available()
    return jsonify({
        'status': 'healthy',
        'message': 'Repository Visualization API is running',
        'git_available': git_available
    }), 200 