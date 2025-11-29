"""Project model."""
from datetime import datetime
from decimal import Decimal
import re

from app.extensions import db


class Project(db.Model):
    """Project/campaign model for crowdfunding."""

    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True, index=True)

    # Basic info
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)

    # Media
    images = db.Column(db.JSON, default=list)  # List of image URLs
    video_url = db.Column(db.String(500), nullable=True)

    # Funding
    goal_sol = db.Column(db.Numeric(18, 9), nullable=False)
    raised_sol = db.Column(db.Numeric(18, 9), default=Decimal('0'))

    # Timeline
    end_date = db.Column(db.DateTime, nullable=False)

    # Status: active, ended, cancelled, banned
    status = db.Column(db.String(20), default='active', index=True)

    # Draft mode - not visible publicly until published
    is_draft = db.Column(db.Boolean, default=False, index=True)

    # Payout status: pending, processing, completed, failed
    payout_status = db.Column(db.String(20), default='pending')
    payout_tx = db.Column(db.String(100), nullable=True)

    # Social links
    project_website = db.Column(db.String(255), nullable=True)
    project_twitter = db.Column(db.String(255), nullable=True)
    project_telegram = db.Column(db.String(255), nullable=True)
    project_github = db.Column(db.String(255), nullable=True)
    project_discord = db.Column(db.String(255), nullable=True)
    project_linkedin = db.Column(db.String(255), nullable=True)
    project_youtube = db.Column(db.String(255), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    donations = db.relationship('Donation', backref='project', lazy='dynamic')
    milestones = db.relationship(
        'Milestone',
        backref='project',
        lazy='dynamic',
        order_by='Milestone.sort_order'
    )
    reward_tiers = db.relationship(
        'RewardTier',
        backref='project',
        lazy='dynamic',
        order_by='RewardTier.sort_order'
    )
    payouts = db.relationship('Payout', backref='project', lazy='dynamic')
    updates = db.relationship(
        'ProjectUpdate',
        backref='project',
        lazy='dynamic',
        order_by='desc(ProjectUpdate.created_at)'
    )
    comments = db.relationship(
        'Comment',
        backref='project',
        lazy='dynamic',
        order_by='desc(Comment.created_at)'
    )

    def __repr__(self):
        return f'<Project {self.title}>'

    @staticmethod
    def generate_slug(title):
        """Generate URL-friendly slug from title."""
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower().strip()
        # Remove special characters
        slug = re.sub(r'[^\w\s-]', '', slug)
        # Replace spaces with hyphens
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:100]

    @property
    def is_active(self):
        """Check if project is still accepting donations."""
        return self.status == 'active' and datetime.utcnow() < self.end_date

    @property
    def is_ended(self):
        """Check if project has ended."""
        return self.status == 'ended' or datetime.utcnow() >= self.end_date

    @property
    def progress_percent(self):
        """Calculate funding progress percentage."""
        if self.goal_sol == 0:
            return 0
        percent = (self.raised_sol / self.goal_sol) * 100
        return min(float(percent), 100)  # Cap at 100 for display

    @property
    def total_progress_percent(self):
        """Calculate total funding progress (can exceed 100%)."""
        if self.goal_sol == 0:
            return 0
        return float((self.raised_sol / self.goal_sol) * 100)

    @property
    def time_remaining(self):
        """Get time remaining until end date."""
        if self.is_ended:
            return None
        return self.end_date - datetime.utcnow()

    @property
    def donation_count(self):
        """Get number of confirmed donations."""
        return self.donations.filter_by(status='confirmed').count()

    @property
    def primary_image(self):
        """Get the first image as primary."""
        if self.images and len(self.images) > 0:
            return self.images[0]
        return None

    def update_raised_amount(self):
        """Recalculate raised amount from confirmed donations."""
        from app.models.donation import Donation
        total = db.session.query(
            db.func.sum(Donation.amount_sol)
        ).filter(
            Donation.project_id == self.id,
            Donation.status == 'confirmed'
        ).scalar()
        self.raised_sol = total or Decimal('0')

    def check_milestones(self):
        """Check and update milestone status based on raised amount."""
        for milestone in self.milestones:
            if not milestone.reached and self.raised_sol >= milestone.amount_sol:
                milestone.reached = True
                milestone.reached_at = datetime.utcnow()

    def to_dict(self, include_donations=False):
        """Convert project to dictionary."""
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'images': self.images or [],
            'video_url': self.video_url,
            'goal_sol': str(self.goal_sol),
            'raised_sol': str(self.raised_sol),
            'progress_percent': self.progress_percent,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'is_active': self.is_active,
            'donation_count': self.donation_count,
            'project_website': self.project_website,
            'project_twitter': self.project_twitter,
            'project_telegram': self.project_telegram,
            'project_github': self.project_github,
            'project_discord': self.project_discord,
            'project_linkedin': self.project_linkedin,
            'project_youtube': self.project_youtube,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'category': self.category.to_dict() if self.category else None,
            'creator': {
                'id': self.creator.id,
                'username': self.creator.username,
                'profile_image': self.creator.profile_image
            },
            'milestones': [m.to_dict() for m in self.milestones.order_by('sort_order')],
            'reward_tiers': [t.to_dict() for t in self.reward_tiers.order_by('sort_order')]
        }

        if include_donations:
            data['donations'] = [
                d.to_dict() for d in self.donations.filter_by(status='confirmed').order_by(
                    db.desc('created_at')
                ).limit(50)
            ]

        return data
