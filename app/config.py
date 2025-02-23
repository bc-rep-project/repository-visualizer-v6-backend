import os
from datetime import timedelta

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Repository settings
    REPO_DIR = os.path.join(os.getcwd(), 'repos')
    
    # CORS settings
    CORS_ORIGINS = [
        "https://repository-visualizer-v6-frontend.vercel.app",
        "http://localhost:3000"  # For local development
    ]
    
    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL')
    RATELIMIT_STORAGE_OPTIONS = {
        "socket_connect_timeout": 30,
        "socket_timeout": 30
    } if os.environ.get('REDIS_URL') else {}
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # MongoDB settings
    MONGO_URI = os.environ.get('DATABASE_URL', 'mongodb://localhost:27017/repo_visualizer')

class DevelopmentConfig(Config):
    DEBUG = True
    MONGO_URI = os.environ.get('DATABASE_URL', 'mongodb://localhost:27017/repo_visualizer_dev')

class ProductionConfig(Config):
    DEBUG = False
    # Use secure Redis configuration in production
    RATELIMIT_STORAGE_OPTIONS = {
        "socket_connect_timeout": 30,
        "socket_timeout": 30,
        "ssl_cert_reqs": None  # Required for Redis SSL connections
    } if os.environ.get('REDIS_URL') else {}

class TestingConfig(Config):
    TESTING = True
    MONGO_URI = os.environ.get('DATABASE_URL', 'mongodb://localhost:27017/repo_visualizer_test')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
