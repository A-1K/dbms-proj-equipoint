import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # PostgreSQL connection URI — format: postgresql://user:password@host:port/dbname
    # SQLite is NOT suitable for production. PostgreSQL gives you proper
    # ACID compliance, concurrent connections, and real ENUM types.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/uni_marketplace'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # PostgreSQL-specific engine options: connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,       # drop stale connections automatically
        'pool_recycle': 300,         # recycle connections every 5 minutes
    }

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super-secret-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = 86400
    SECRET_KEY = os.getenv('SECRET_KEY', 'flask-secret-change-me')
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
