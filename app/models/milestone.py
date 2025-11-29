"""Milestone model."""
from datetime import datetime

from app.extensions import db


class Milestone(db.Model):
    """Milestone (stretch goal) model for projects."""

    __tablename__ = 'milestones'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True)

    # Goal amount
    amount_sol = db.Column(db.Numeric(18, 9), nullable=False)

    # Content
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Status
    reached = db.Column(db.Boolean, default=False)
    reached_at = db.Column(db.DateTime, nullable=True)

    # Display order
    sort_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Milestone {self.title} at {self.amount_sol} SOL>'

    def to_dict(self):
        """Convert milestone to dictionary."""
        return {
            'id': self.id,
            'amount_sol': str(self.amount_sol),
            'title': self.title,
            'description': self.description,
            'reached': self.reached,
            'reached_at': self.reached_at.isoformat() if self.reached_at else None,
            'sort_order': self.sort_order
        }
