"""Notification model."""
from datetime import datetime

from app.extensions import db


class Notification(db.Model):
    """In-app notification model."""

    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Notification type: donation, comment, reply, milestone, project_ended, payout
    type = db.Column(db.String(50), nullable=False)

    # Title and message
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(500), nullable=True)

    # Link to related resource
    link = db.Column(db.String(500), nullable=True)

    # Related IDs for context
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    donation_id = db.Column(db.Integer, nullable=True)
    comment_id = db.Column(db.Integer, nullable=True)

    # Status
    is_read = db.Column(db.Boolean, default=False, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    project = db.relationship('Project', backref=db.backref('notifications', lazy='dynamic'))

    def __repr__(self):
        return f'<Notification {self.type} for user {self.user_id}>'

    def to_dict(self):
        """Convert notification to dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'project': {
                'id': self.project.id,
                'title': self.project.title,
                'slug': self.project.slug
            } if self.project else None
        }

    @staticmethod
    def create_notification(user_id, type, title, message=None, link=None,
                           project_id=None, donation_id=None, comment_id=None):
        """Helper to create a notification."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            link=link,
            project_id=project_id,
            donation_id=donation_id,
            comment_id=comment_id
        )
        db.session.add(notification)
        return notification

    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications for a user."""
        return Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()

    @staticmethod
    def mark_all_read(user_id):
        """Mark all notifications as read for a user."""
        Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()
