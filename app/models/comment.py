"""Comment model."""
from datetime import datetime
from app.extensions import db


class Comment(db.Model):
    """Comments on projects."""

    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True, index=True)

    content = db.Column(db.Text, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref='comments')
    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<Comment {self.id}>'

    @property
    def reply_count(self):
        """Get number of replies."""
        return self.replies.count()

    def to_dict(self, include_replies=False):
        """Convert comment to dictionary."""
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reply_count': self.reply_count,
            'author': {
                'id': self.author.id,
                'username': self.author.username,
                'profile_image': self.author.profile_image
            }
        }

        if include_replies:
            data['replies'] = [r.to_dict() for r in self.replies.order_by(Comment.created_at.asc())]

        return data
