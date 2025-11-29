"""Payout model."""
from datetime import datetime

from app.extensions import db


class Payout(db.Model):
    """Payout model for tracking creator payments."""

    __tablename__ = 'payouts'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True)

    # Amounts
    total_raised = db.Column(db.Numeric(18, 9), nullable=False)
    platform_fee = db.Column(db.Numeric(18, 9), nullable=False)  # 2.5%
    net_amount = db.Column(db.Numeric(18, 9), nullable=False)  # 97.5%

    # Transaction details
    recipient_wallet = db.Column(db.String(44), nullable=False)
    tx_signature = db.Column(db.String(100), nullable=True, unique=True)

    # Status: pending, processing, completed, failed
    status = db.Column(db.String(20), default='pending', index=True)
    error_message = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Payout {self.net_amount} SOL for project {self.project_id}>'

    @property
    def explorer_url(self):
        """Get Solana explorer URL for transaction."""
        if not self.tx_signature:
            return None
        from flask import current_app
        if current_app.config.get('USE_DEVNET'):
            return f'https://explorer.solana.com/tx/{self.tx_signature}?cluster=devnet'
        return f'https://explorer.solana.com/tx/{self.tx_signature}'

    def to_dict(self):
        """Convert payout to dictionary."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'total_raised': str(self.total_raised),
            'platform_fee': str(self.platform_fee),
            'net_amount': str(self.net_amount),
            'recipient_wallet': self.recipient_wallet,
            'tx_signature': self.tx_signature,
            'explorer_url': self.explorer_url,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
