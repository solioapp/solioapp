"""User model."""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    """User model for authentication and profiles."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    bio = db.Column(db.String(250), nullable=True)
    profile_image = db.Column(db.String(500), nullable=True)
    wallet_address = db.Column(db.String(44), nullable=True, index=True)

    # Auth type: email, google, twitter, wallet
    auth_type = db.Column(db.String(20), nullable=False, default='email')

    # OAuth IDs
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    twitter_id = db.Column(db.String(255), unique=True, nullable=True)

    # Email verification
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), nullable=True)

    # Password reset
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)

    # Admin flag
    is_admin = db.Column(db.Boolean, default=False)

    # Social links
    twitter_url = db.Column(db.String(255), nullable=True)
    telegram_url = db.Column(db.String(255), nullable=True)
    discord_url = db.Column(db.String(255), nullable=True)
    website_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    youtube_url = db.Column(db.String(255), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = db.relationship('Project', backref='creator', lazy='dynamic')
    donations = db.relationship('Donation', backref='donor', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def has_payout_wallet(self):
        """Check if user has a wallet address for payouts."""
        return bool(self.wallet_address)

    def to_dict(self, include_private=False):
        """Convert user to dictionary."""
        data = {
            'id': self.id,
            'username': self.username,
            'bio': self.bio,
            'profile_image': self.profile_image,
            'twitter_url': self.twitter_url,
            'telegram_url': self.telegram_url,
            'discord_url': self.discord_url,
            'website_url': self.website_url,
            'github_url': self.github_url,
            'linkedin_url': self.linkedin_url,
            'youtube_url': self.youtube_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

        if include_private:
            data.update({
                'email': self.email,
                'email_verified': self.email_verified,
                'wallet_address': self.wallet_address,
                'auth_type': self.auth_type
            })

        return data


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))
