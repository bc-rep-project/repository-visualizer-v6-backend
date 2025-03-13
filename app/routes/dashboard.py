from flask import Blueprint, jsonify
from app import mongo, limiter
from datetime import datetime, timedelta
import random

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
@limiter.limit("30/minute")
def get_dashboard_stats():
    """Get dashboard statistics."""
    # Get repository stats
    total_repos = mongo.db.repositories.count_documents({})
    completed_repos = mongo.db.repositories.count_documents({'status': 'completed'})
    pending_repos = mongo.db.repositories.count_documents({'status': 'pending'})
    failed_repos = mongo.db.repositories.count_documents({'status': 'failed'})
    
    # Get language distribution
    language_distribution = []
    languages_cursor = mongo.db.repositories.aggregate([
        {'$match': {'status': 'completed'}},
        {'$project': {'languages': {'$objectToArray': '$languages'}}},
        {'$unwind': '$languages'},
        {'$group': {'_id': '$languages.k', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ])
    
    languages = list(languages_cursor)
    total_count = sum(lang['count'] for lang in languages)
    
    for lang in languages:
        percentage = (lang['count'] / total_count * 100) if total_count > 0 else 0
        language_distribution.append({
            'language': lang['_id'],
            'count': lang['count'],
            'percentage': percentage
        })
    
    # Get recent activity (mock data for now)
    now = datetime.utcnow()
    recent_activity = [
        {
            'type': 'Repository Analysis',
            'repository': 'frontend-v2',
            'timestamp': (now - timedelta(hours=2)).isoformat(),
            'details': 'Analysis completed successfully'
        },
        {
            'type': 'Repository Added',
            'repository': 'api-service',
            'timestamp': (now - timedelta(hours=5)).isoformat(),
            'details': 'New repository added to the system'
        },
        {
            'type': 'Report Generated',
            'repository': 'mobile-app',
            'timestamp': (now - timedelta(days=1)).isoformat(),
            'details': 'Code quality report generated'
        }
    ]
    
    return jsonify({
        'repository_stats': {
            'total': total_repos,
            'completed': completed_repos,
            'pending': pending_repos,
            'failed': failed_repos
        },
        'language_distribution': language_distribution,
        'recent_activity': recent_activity
    }), 200 