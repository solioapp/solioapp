"""Main routes - homepage and static pages."""
from flask import Blueprint, render_template

from app.models import Project

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with featured projects."""
    # Get active projects, ordered by raised amount (most funded first)
    featured_projects = Project.query.filter_by(status='active').order_by(
        Project.raised_sol.desc()
    ).limit(6).all()

    # Get newest projects
    newest_projects = Project.query.filter_by(status='active').order_by(
        Project.created_at.desc()
    ).limit(6).all()

    return render_template(
        'index.html',
        featured_projects=featured_projects,
        newest_projects=newest_projects
    )


@main_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@main_bp.route('/faq')
def faq():
    """FAQ page."""
    return render_template('faq.html')


@main_bp.route('/terms')
def terms():
    """Terms of service page."""
    return render_template('terms.html')


@main_bp.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('privacy.html')


@main_bp.route('/roadmap')
def roadmap():
    """Roadmap and token utility page."""
    return render_template('roadmap.html')
