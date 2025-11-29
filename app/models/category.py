"""Category model."""
from app.extensions import db


class Category(db.Model):
    """Category for project classification."""

    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    icon = db.Column(db.String(50), nullable=True)  # Icon identifier or emoji
    color = db.Column(db.String(20), nullable=True)  # CSS color for styling
    description = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, default=0)

    # Relationships
    projects = db.relationship('Project', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

    @property
    def project_count(self):
        """Get number of active projects in this category."""
        return self.projects.filter_by(status='active').count()

    def to_dict(self):
        """Convert category to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'icon': self.icon,
            'color': self.color,
            'description': self.description,
            'project_count': self.project_count
        }


# Default categories to seed
DEFAULT_CATEGORIES = [
    {'name': 'Gaming', 'slug': 'gaming', 'icon': '🎮', 'color': '#8b5cf6', 'description': 'Video games, esports, and gaming content'},
    {'name': 'Art', 'slug': 'art', 'icon': '🎨', 'color': '#ec4899', 'description': 'Visual art, illustrations, and creative projects'},
    {'name': 'Technology', 'slug': 'technology', 'icon': '💻', 'color': '#06b6d4', 'description': 'Software, hardware, and tech innovations'},
    {'name': 'Music', 'slug': 'music', 'icon': '🎵', 'color': '#f59e0b', 'description': 'Music production, albums, and audio projects'},
    {'name': 'Film', 'slug': 'film', 'icon': '🎬', 'color': '#ef4444', 'description': 'Movies, documentaries, and video content'},
    {'name': 'Design', 'slug': 'design', 'icon': '✨', 'color': '#10b981', 'description': 'Product design, UX/UI, and creative design'},
    {'name': 'Community', 'slug': 'community', 'icon': '🤝', 'color': '#3b82f6', 'description': 'Community projects and social initiatives'},
    {'name': 'Other', 'slug': 'other', 'icon': '📦', 'color': '#6b7280', 'description': 'Projects that don\'t fit other categories'},
]
