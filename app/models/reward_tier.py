"""Reward Tier model for project rewards/perks."""
from datetime import datetime
from decimal import Decimal

from app.extensions import db


class RewardTier(db.Model):
    """Reward tier model for project perks/rewards."""

    __tablename__ = 'reward_tiers'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True)

    # Tier info
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    min_amount_sol = db.Column(db.Numeric(18, 9), nullable=False)

    # Limits (optional)
    max_claims = db.Column(db.Integer, nullable=True)  # None = unlimited
    claimed_count = db.Column(db.Integer, default=0)

    # Sorting
    sort_order = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    donations = db.relationship('Donation', backref='reward_tier', lazy='dynamic')

    def __repr__(self):
        return f'<RewardTier {self.title} ({self.min_amount_sol} SOL)>'

    @property
    def is_available(self):
        """Check if tier is still available (not sold out)."""
        if self.max_claims is None:
            return True
        return self.claimed_count < self.max_claims

    @property
    def remaining_count(self):
        """Get remaining available claims."""
        if self.max_claims is None:
            return None
        return max(0, self.max_claims - self.claimed_count)

    def claim(self):
        """Increment claimed count."""
        self.claimed_count += 1

    def to_dict(self):
        """Convert tier to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'min_amount_sol': str(self.min_amount_sol),
            'max_claims': self.max_claims,
            'claimed_count': self.claimed_count,
            'is_available': self.is_available,
            'remaining_count': self.remaining_count,
            'sort_order': self.sort_order
        }
