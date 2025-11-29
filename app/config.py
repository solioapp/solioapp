"""Application configuration."""
import os
from datetime import timedelta


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://localhost/solio'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Solana
    SOLANA_RPC_URL = os.environ.get(
        'SOLANA_RPC_URL',
        'https://api.mainnet-beta.solana.com'
    )
    SOLANA_DEVNET_RPC_URL = os.environ.get(
        'SOLANA_DEVNET_RPC_URL',
        'https://api.devnet.solana.com'
    )
    PLATFORM_WALLET_ADDRESS = os.environ.get('PLATFORM_WALLET_ADDRESS', '')
    PLATFORM_WALLET_SECRET = os.environ.get('PLATFORM_WALLET_SECRET', '')
    PLATFORM_FEE_PERCENT = 2.5

    # Use devnet for development
    USE_DEVNET = os.environ.get('USE_DEVNET', 'true').lower() == 'true'

    # OAuth - Google
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    # OAuth - Twitter/X
    TWITTER_CLIENT_ID = os.environ.get('TWITTER_CLIENT_ID', '')
    TWITTER_CLIENT_SECRET = os.environ.get('TWITTER_CLIENT_SECRET', '')

    # Base URL for email links
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.sendgrid.net')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@solio.io')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@solio.io')

    # Storage (Cloudinary)
    CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')

    # Upload limits
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_HEADERS_ENABLED = True

    # Wallet auth
    WALLET_NONCE_EXPIRY_MINUTES = 10

    # Payout scheduler
    PAYOUT_CHECK_INTERVAL_MINUTES = 5

    # Price cache
    SOL_PRICE_CACHE_SECONDS = 60


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SESSION_COOKIE_SECURE = False
    # USE_DEVNET is read from environment (defaults to true in base Config)

    # Use SQLite for local development (no PostgreSQL needed)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///solio_dev.db'
    )
    # SQLite doesn't support pool options
    SQLALCHEMY_ENGINE_OPTIONS = {}


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    USE_DEVNET = False

    # Ensure these are set in production
    @classmethod
    def init_app(cls, app):
        assert os.environ.get('SECRET_KEY'), 'SECRET_KEY must be set'
        assert os.environ.get('DATABASE_URL'), 'DATABASE_URL must be set'
        assert os.environ.get('PLATFORM_WALLET_ADDRESS'), 'PLATFORM_WALLET_ADDRESS must be set'
        assert os.environ.get('PLATFORM_WALLET_SECRET'), 'PLATFORM_WALLET_SECRET must be set'


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    USE_DEVNET = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
