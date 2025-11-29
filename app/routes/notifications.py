"""Notification routes."""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Notification

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/')
@login_required
def list_notifications():
    """List all notifications for the user."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    notifications = current_user.notifications.order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'notifications/list.html',
        notifications=notifications.items,
        pagination=notifications
    )


@notifications_bp.route('/api/list')
@login_required
def api_list():
    """API endpoint for notifications list."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    query = current_user.notifications.order_by(Notification.created_at.desc())

    if unread_only:
        query = query.filter_by(is_read=False)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'unread_count': Notification.get_unread_count(current_user.id)
    })


@notifications_bp.route('/api/unread-count')
@login_required
def api_unread_count():
    """Get unread notification count."""
    return jsonify({
        'count': Notification.get_unread_count(current_user.id)
    })


@notifications_bp.route('/api/<int:id>/read', methods=['POST'])
@login_required
def api_mark_read(id):
    """Mark a notification as read."""
    notification = Notification.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    notification.is_read = True
    db.session.commit()

    return jsonify({'success': True})


@notifications_bp.route('/api/mark-all-read', methods=['POST'])
@login_required
def api_mark_all_read():
    """Mark all notifications as read."""
    Notification.mark_all_read(current_user.id)
    return jsonify({'success': True})


@notifications_bp.route('/api/<int:id>', methods=['DELETE'])
@login_required
def api_delete(id):
    """Delete a notification."""
    notification = Notification.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(notification)
    db.session.commit()

    return jsonify({'success': True})
