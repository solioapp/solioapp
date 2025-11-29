"""Wallet nonce model for authentication."""
from datetime import datetime, timedelta
import secrets

from app.extensions import db


class WalletNonce(db.Model):
    """Wallet nonce model for secure wallet authentication."""

    __tablename__ = 'wallet_nonces'

    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(44), nullable=False, index=True)
    nonce = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<WalletNonce for {self.wallet_address}>'

    @classmethod
    def generate(cls, wallet_address, expiry_minutes=10):
        """Generate a new nonce for wallet authentication."""
        nonce = secrets.token_hex(32)
        expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

        instance = cls(
            wallet_address=wallet_address,
            nonce=nonce,
            expires_at=expires_at
        )

        return instance

    @property
    def is_valid(self):
        """Check if nonce is valid (not expired and not used)."""
        return not self.used and datetime.utcnow() < self.expires_at

    @property
    def message_to_sign(self):
        """Get the message that should be signed by the wallet."""
        return f"Sign this message to authenticate with Solio.\n\nNonce: {self.nonce}"

    def mark_used(self):
        """Mark nonce as used."""
        self.used = True

    @classmethod
    def cleanup_expired(cls):
        """Delete expired nonces."""
        cls.query.filter(
            cls.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
