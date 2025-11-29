"""Admin routes for project management."""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Project, User, Donation

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with project overview."""
    # Stats
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='active').count()
    banned_projects = Project.query.filter_by(status='banned').count()
    total_users = User.query.count()
    total_donations = Donation.query.filter_by(status='confirmed').count()

    # Recent projects
    projects = Project.query.order_by(Project.created_at.desc()).limit(50).all()

    return render_template(
        'admin/dashboard.html',
        total_projects=total_projects,
        active_projects=active_projects,
        banned_projects=banned_projects,
        total_users=total_users,
        total_donations=total_donations,
        projects=projects
    )


@admin_bp.route('/projects')
@login_required
@admin_required
def projects():
    """List all projects with filters."""
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Project.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    projects = query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        'admin/projects.html',
        projects=projects,
        status_filter=status_filter
    )


@admin_bp.route('/projects/<int:project_id>/ban', methods=['POST'])
@login_required
@admin_required
def ban_project(project_id):
    """Ban a project."""
    project = Project.query.get_or_404(project_id)

    if project.status == 'banned':
        flash('Project is already banned.', 'warning')
    else:
        project.status = 'banned'
        db.session.commit()
        flash(f'Project "{project.title}" has been banned.', 'success')

    return redirect(url_for('admin.projects'))


@admin_bp.route('/projects/<int:project_id>/unban', methods=['POST'])
@login_required
@admin_required
def unban_project(project_id):
    """Unban a project."""
    project = Project.query.get_or_404(project_id)

    if project.status != 'banned':
        flash('Project is not banned.', 'warning')
    else:
        project.status = 'active'
        db.session.commit()
        flash(f'Project "{project.title}" has been unbanned.', 'success')

    return redirect(url_for('admin.projects'))


@admin_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_project(project_id):
    """Delete a project and its related data."""
    project = Project.query.get_or_404(project_id)

    # Delete related data
    Donation.query.filter_by(project_id=project_id).delete()

    # Delete milestones
    from app.models import Milestone
    Milestone.query.filter_by(project_id=project_id).delete()

    # Delete payouts
    from app.models import Payout
    Payout.query.filter_by(project_id=project_id).delete()

    project_title = project.title
    db.session.delete(project)
    db.session.commit()

    flash(f'Project "{project_title}" has been deleted.', 'success')
    return redirect(url_for('admin.projects'))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user."""
    if user_id == current_user.id:
        flash('You cannot change your own admin status.', 'error')
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()

    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin status for {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))
