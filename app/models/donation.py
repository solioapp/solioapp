"""Donation model."""
from datetime import datetime
from decimal import Decimal

from app.extensions import db


class Donation(db.Model):
    """Donation model for tracking contributions."""

    __tablename__ = 'donations'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    reward_tier_id = db.Column(db.Integer, db.ForeignKey('reward_tiers.id'), nullable=True, index=True)

    # Amount
    amount_sol = db.Column(db.Numeric(18, 9), nullable=False)
    platform_fee = db.Column(db.Numeric(18, 9), nullable=True)  # Calculated 2.5%

    # Message from donor
    message = db.Column(db.Text, nullable=True)

    # Donor contact (for reward fulfillment)
    donor_email = db.Column(db.String(255), nullable=True)

    # Blockchain data
    tx_signature = db.Column(db.String(100), unique=True, nullable=False, index=True)
    donor_wallet = db.Column(db.String(44), nullable=False)

    # Status: pending, confirmed, failed
    status = db.Column(db.String(20), default='pending', index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<Donation {self.amount_sol} SOL to project {self.project_id}>'

    @property
    def is_anonymous(self):
        """Check if donation is anonymous (no logged-in user)."""
        return self.user_id is None

    @property
    def donor_display_name(self):
        """Get display name for donor."""
        if self.donor:
            return self.donor.username
        return 'Anonymous'

    @property
    def explorer_url(self):
        """Get Solana explorer URL for transaction."""
        from flask import current_app
        if current_app.config.get('USE_DEVNET'):
            return f'https://explorer.solana.com/tx/{self.tx_signature}?cluster=devnet'
        return f'https://explorer.solana.com/tx/{self.tx_signature}'

    def calculate_fee(self, fee_percent=2.5):
        """Calculate platform fee."""
        self.platform_fee = self.amount_sol * Decimal(str(fee_percent)) / Decimal('100')

    def to_dict(self, include_email=False):
        """Convert donation to dictionary."""
        data = {
            'id': self.id,
            'amount_sol': str(self.amount_sol),
            'message': self.message,
            'tx_signature': self.tx_signature,
            'donor_wallet': self.donor_wallet,
            'donor_name': self.donor_display_name,
            'is_anonymous': self.is_anonymous,
            'explorer_url': self.explorer_url,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reward_tier': self.reward_tier.to_dict() if self.reward_tier else None
        }
        if include_email and self.donor_email:
            data['donor_email'] = self.donor_email
        return data
