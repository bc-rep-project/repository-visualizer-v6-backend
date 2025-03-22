from flask import Blueprint, jsonify, request
from app import limiter, mongo
from app.services.auto_save_service import AutoSaveService
from datetime import datetime
from bson import ObjectId

auto_save_bp = Blueprint('auto_save', __name__, url_prefix='/api/repositories/auto-save')

@auto_save_bp.route('/status', methods=['GET'])
@limiter.limit("60/minute")
def get_auto_save_status():
    """Get the current status of the auto-save feature."""
    status = AutoSaveService.get_status()
    return jsonify(status), 200

@auto_save_bp.route('/start', methods=['POST'])
@limiter.limit("10/minute")
def start_auto_save():
    """Start the auto-save background process."""
    data = request.get_json() or {}
    
    # Get interval from request body if provided
    interval = data.get('interval')
    if interval is not None:
        try:
            interval = int(interval)
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Invalid interval value. Must be an integer representing seconds.'
            }), 400
    
    result = AutoSaveService.start_auto_save(interval)
    return jsonify(result), 200

@auto_save_bp.route('/stop', methods=['POST'])
@limiter.limit("10/minute")
def stop_auto_save():
    """Stop the auto-save background process."""
    result = AutoSaveService.stop_auto_save()
    return jsonify(result), 200

@auto_save_bp.route('/run', methods=['POST'])
@limiter.limit("5/minute")
def run_auto_save():
    """Manually run the auto-save process once."""
    result = AutoSaveService.run_auto_save()
    return jsonify(result), 200

@auto_save_bp.route('/<repo_id>', methods=['POST'])
@limiter.limit("20/minute")
def save_repository(repo_id):
    """Manually save a specific repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    result = AutoSaveService.save_repository(repo_id)
    return jsonify(result), 200

@auto_save_bp.route('/backups', methods=['GET'])
@limiter.limit("30/minute")
def get_backups():
    """Get information about all backed up repositories."""
    try:
        # Count total backups
        backups_count = mongo.db.repository_backups.count_documents({})

        # Get the most recent backups with pagination
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit

        backups = list(mongo.db.repository_backups.find().sort('backed_up_at', -1).skip(offset).limit(limit))
        
        # Convert ObjectId to string for JSON serialization and format dates
        for backup in backups:
            backup['_id'] = str(backup['_id'])
            backup['repository_id'] = str(backup['repository_id'])
            if 'structure' in backup:
                # Remove structure to avoid sending large data
                backup.pop('structure', None)
        
        # Get some statistics about backups
        first_backup_date = None
        last_backup_date = None
        if backups_count > 0:
            first_backup = mongo.db.repository_backups.find_one({}, sort=[('backed_up_at', 1)])
            last_backup = mongo.db.repository_backups.find_one({}, sort=[('backed_up_at', -1)])
            
            if first_backup and 'backed_up_at' in first_backup:
                first_backup_date = first_backup['backed_up_at']
            if last_backup and 'backed_up_at' in last_backup:
                last_backup_date = last_backup['backed_up_at']
        
        return jsonify({
            'total': backups_count,
            'backups': backups,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': backups_count,
                'pages': (backups_count + limit - 1) // limit
            },
            'statistics': {
                'first_backup': first_backup_date,
                'last_backup': last_backup_date,
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auto_save_bp.route('/backups/<backup_id>', methods=['GET'])
@limiter.limit("30/minute")
def get_backup_details(backup_id):
    """Get detailed information about a specific backup."""
    try:
        # Validate backup_id
        if not ObjectId.is_valid(backup_id):
            return jsonify({'error': f'Invalid backup ID: {backup_id}'}), 400
            
        # Find the backup
        backup = mongo.db.repository_backups.find_one({'_id': ObjectId(backup_id)})
        if not backup:
            return jsonify({'error': f'Backup not found: {backup_id}'}), 404
            
        # Convert ObjectId to string for JSON serialization
        backup['_id'] = str(backup['_id'])
        backup['repository_id'] = str(backup['repository_id'])
        
        return jsonify(backup), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 