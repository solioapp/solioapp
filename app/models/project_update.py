"""Project Update model."""
from datetime import datetime
from app.extensions import db


class ProjectUpdate(db.Model):
    """Updates/news posts for projects."""

    __tablename__ = 'project_updates'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref='project_updates')

    def __repr__(self):
        return f'<ProjectUpdate {self.title}>'

    def to_dict(self):
        """Convert update to dictionary."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'author': {
                'id': self.author.id,
                'username': self.author.username,
                'profile_image': self.author.profile_image
            }
        }
