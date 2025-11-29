"""Custom decorators."""
from functools import wraps
from flask import abort, jsonify, request
from flask_login import current_user


def owner_required(model_class, id_param='id'):
    """
    Decorator to ensure current user owns the resource.

    Usage:
        @owner_required(Project)
        def edit_project(id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Unauthorized'}), 401
                abort(401)

            resource_id = kwargs.get(id_param)
            resource = model_class.query.get_or_404(resource_id)

            # Check ownership
            if hasattr(resource, 'user_id'):
                if resource.user_id != current_user.id:
                    if request.is_json:
                        return jsonify({'error': 'Forbidden'}), 403
                    abort(403)
            elif hasattr(resource, 'creator_id'):
                if resource.creator_id != current_user.id:
                    if request.is_json:
                        return jsonify({'error': 'Forbidden'}), 403
                    abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def json_required(f):
    """Decorator to ensure request has JSON content type."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function


def wallet_required(f):
    """Decorator to ensure user has a wallet address configured."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Unauthorized'}), 401
            abort(401)

        if not current_user.wallet_address:
            if request.is_json:
                return jsonify({'error': 'Wallet address required'}), 400
            abort(400)

        return f(*args, **kwargs)
    return decorated_function
