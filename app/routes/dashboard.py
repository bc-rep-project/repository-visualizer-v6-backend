from flask import Blueprint, jsonify
from app import mongo, limiter
from datetime import datetime, timedelta
import logging

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
@limiter.limit("30/minute")
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        # Get repository stats
        total_repos = mongo.db.repositories.count_documents({})
        completed_repos = mongo.db.repositories.count_documents({'status': 'completed'})
        pending_repos = mongo.db.repositories.count_documents({'status': 'pending'})
        failed_repos = mongo.db.repositories.count_documents({'status': 'failed'})
        
        # Get language distribution
        language_distribution = []
        
        # This approach handles different language field formats
        repositories = list(mongo.db.repositories.find(
            {'status': 'completed'}, 
            {'languages': 1}
        ))
        
        language_counts = {}
        
        for repo in repositories:
            languages = repo.get('languages', {})
            if isinstance(languages, dict):
                for lang, count in languages.items():
                    # Clean up language name (remove file extension if present)
                    lang_name = lang.split('.')[-1] if '.' in lang else lang
                    if lang_name not in language_counts:
                        language_counts[lang_name] = 0
                    language_counts[lang_name] += 1
        
        # Sort languages by count and get top languages
        sorted_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
        total_count = sum(language_counts.values())
        
        for lang, count in sorted_languages:
            percentage = (count / total_count * 100) if total_count > 0 else 0
            language_distribution.append({
                'language': lang,
                'count': count,
                'percentage': percentage
            })
        
        # Get recent activity from repository updates
        recent_activity = []
        
        # Get actual recent activity from database
        recent_repos = mongo.db.repositories.find().sort('updated_at', -1).limit(5)
        
        for repo in recent_repos:
            activity_type = 'Repository Analysis'
            details = 'Analysis completed'
            
            if repo.get('status') == 'completed':
                activity_type = 'Analysis Completed'
                details = f"Analyzed {repo.get('file_count', 0)} files in {repo.get('directory_count', 0)} directories"
            elif repo.get('status') == 'pending':
                activity_type = 'Repository Added'
                details = 'Waiting for analysis to complete'
            elif repo.get('status') == 'failed':
                activity_type = 'Analysis Failed'
                details = 'Repository analysis encountered an error'
            
            # Format the timestamp or use current time as fallback
            timestamp = repo.get('updated_at', datetime.utcnow().isoformat())
            
            recent_activity.append({
                'type': activity_type,
                'repository': repo.get('repo_url', '').split('/')[-1] if repo.get('repo_url') else 'Unknown',
                'timestamp': timestamp,
                'details': details
            })
        
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
        
    except Exception as e:
        logging.error(f"Error generating dashboard stats: {str(e)}")
        return jsonify({
            'repository_stats': {
                'total': 0,
                'completed': 0,
                'pending': 0,
                'failed': 0
            },
            'language_distribution': [],
            'recent_activity': []
        }), 500 