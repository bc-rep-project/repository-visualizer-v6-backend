import os
from datetime import timedelta

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    MONGO_URI = os.environ.get('DATABASE_URL', 'mongodb://localhost:27017/repo_visualizer')
    MONGO_TLS = os.environ.get('MONGO_TLS', 'false').lower() == 'true'
    MONGO_TLS_INSECURE = os.environ.get('MONGO_TLS_INSECURE', 'false').lower() == 'true'
    CORS_ORIGINS = eval(os.environ.get('CORS_ORIGINS', '["http://localhost:3000"]'))
    REDIS_URL = os.environ.get('REDIS_URL', None)
    RATELIMIT_STORAGE_OPTIONS = {}
    REPO_STORAGE_DIR = os.environ.get('REPO_STORAGE_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'repos'))
    
    # Repository settings
    REPO_DIR = os.path.join(os.getcwd(), 'repos')
    
    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # MongoDB settings
    MONGO_CONNECT_TIMEOUT_MS = 30000
    MONGO_SOCKET_TIMEOUT_MS = 30000
    MONGO_SERVER_SELECTION_TIMEOUT_MS = 30000

class DevelopmentConfig(Config):
    DEBUG = True
    MONGO_URI = os.environ.get('DATABASE_URL', 'mongodb://localhost:27017/repo_visualizer_dev')
    MONGO_TLS = False
    MONGO_TLS_INSECURE = False

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
    MONGO_TLS = False
    MONGO_TLS_INSECURE = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
