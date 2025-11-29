"""Flask extensions initialization."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth

# Database
db = SQLAlchemy()

# Migrations
migrate = Migrate()

# Authentication
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# OAuth
oauth = OAuth()

# Mail
mail = Mail()

# CSRF Protection
csrf = CSRFProtect()

# Rate Limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour"],
    default_limits_exempt_when=lambda: False
)


def init_oauth(app):
    """Initialize OAuth providers."""
    oauth.init_app(app)

    # Google OAuth
    if app.config.get('GOOGLE_CLIENT_ID'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )

    # Twitter/X OAuth 2.0
    if app.config.get('TWITTER_CLIENT_ID'):
        oauth.register(
            name='twitter',
            client_id=app.config['TWITTER_CLIENT_ID'],
            client_secret=app.config['TWITTER_CLIENT_SECRET'],
            api_base_url='https://api.twitter.com/2/',
            access_token_url='https://api.twitter.com/2/oauth2/token',
            authorize_url='https://twitter.com/i/oauth2/authorize',
            client_kwargs={
                'scope': 'tweet.read users.read offline.access'
            }
        )
