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
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_STORAGE_OPTIONS = {"socket_connect_timeout": 30} if os.environ.get('REDIS_URL') else {}
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/repo_visualizer')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Add production-specific settings here

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/repo_visualizer_test'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
