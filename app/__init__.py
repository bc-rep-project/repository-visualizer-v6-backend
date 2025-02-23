from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import config

# Initialize extensions
mongo = PyMongo()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config[config_name])
    
    # Initialize CORS with more specific configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    
    # Initialize extensions
    mongo.init_app(app)
    limiter.init_app(app)
    
    # Register blueprints
    from .routes import repo_bp, health_bp
    app.register_blueprint(repo_bp)
    app.register_blueprint(health_bp)
    
    return app
