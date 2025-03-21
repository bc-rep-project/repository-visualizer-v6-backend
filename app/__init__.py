from flask import Flask, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
import os
from app.utils.json_encoder import MongoJSONEncoder
from app.config import config

# Initialize extensions
mongo = None
limiter = None

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Disable strict slashes to prevent redirects between /path and /path/
    app.url_map.strict_slashes = False
    
    # Use custom JSON encoder
    app.json_encoder = MongoJSONEncoder
    
    # Initialize CORS with proper configuration
    CORS(app, 
         resources={r"/*": {"origins": app.config['CORS_ORIGINS']}}, 
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    
    # Initialize MongoDB
    global mongo
    mongo_options = {}
    if app.config.get('MONGO_TLS'):
        mongo_options['tls'] = app.config['MONGO_TLS']
        if app.config.get('MONGO_TLS_INSECURE'):
            mongo_options['tlsAllowInvalidCertificates'] = app.config['MONGO_TLS_INSECURE']

    # Create a function to get MongoDB connection to avoid fork-safety issues
    def get_mongo_connection():
        client = MongoClient(app.config['MONGO_URI'], **mongo_options)
        db_name = app.config['MONGO_URI'].split('/')[-1]
        if '?' in db_name:
            db_name = db_name.split('?')[0]
        return client[db_name]
    
    # Initialize mongo to the connection function to be called after forking
    app.config['get_mongo_connection'] = get_mongo_connection
    
    # Create initial connection for use before any forking
    mongo = get_mongo_connection()
    
    # Initialize rate limiter
    global limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config['REDIS_URL'] if app.config.get('REDIS_URL') else None,
        storage_options=app.config['RATELIMIT_STORAGE_OPTIONS']
    )
    
    # Configure repository storage
    repo_storage_dir = os.environ.get('REPO_STORAGE_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'repos'))
    os.makedirs(repo_storage_dir, exist_ok=True)
    app.config['REPO_STORAGE_DIR'] = repo_storage_dir
    
    # Import blueprints - moved inside function to avoid circular imports
    from app.routes.health import health_bp, root_bp
    from app.routes.repositories import repo_bp
    from app.routes.repository_details import repo_details_bp
    from app.routes.repository_analysis import repo_analysis_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.search import search_bp
    from app.routes.settings import settings_bp
    from app.routes.notifications import notifications_bp
    
    # Register blueprints
    app.register_blueprint(root_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(repo_bp)
    app.register_blueprint(repo_details_bp)
    app.register_blueprint(repo_analysis_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(notifications_bp)
    
    @app.errorhandler(500)
    def handle_500(error):
        return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500
    
    return app
