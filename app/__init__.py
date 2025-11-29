"""Flask application factory."""
import os
from flask import Flask

from app.config import config
from app.extensions import db, migrate, login_manager, mail, csrf, limiter, init_oauth


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    init_oauth(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.projects import projects_bp
    from app.routes.donations import donations_bp
    from app.routes.profile import profile_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp
    from app.routes.notifications import notifications_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(donations_bp, url_prefix='/donations')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_cli_commands(app)

    # Context processors
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates."""
        from flask_login import current_user
        from app.models import Notification

        data = {
            'platform_name': 'Solio',
            'platform_fee_percent': app.config.get('PLATFORM_FEE_PERCENT', 2.5)
        }

        # Add unread notification count for logged-in users
        if current_user.is_authenticated:
            data['unread_notifications'] = Notification.get_unread_count(current_user.id)
        else:
            data['unread_notifications'] = 0

        return data

    return app


def register_error_handlers(app):
    """Register error handlers."""
    from flask import render_template, jsonify, request

    @app.errorhandler(400)
    def bad_request(error):
        if request.is_json:
            return jsonify({'error': 'Bad request'}), 400
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized(error):
        if request.is_json:
            return jsonify({'error': 'Unauthorized'}), 401
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden(error):
        if request.is_json:
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.is_json:
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(429)
    def rate_limited(error):
        if request.is_json:
            return jsonify({'error': 'Too many requests'}), 429
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500


def register_cli_commands(app):
    """Register CLI commands."""
    import click

    @app.cli.command('init-db')
    def init_db():
        """Initialize the database."""
        db.create_all()
        click.echo('Database initialized.')

    @app.cli.command('cleanup-nonces')
    def cleanup_nonces():
        """Clean up expired wallet nonces."""
        from app.models import WalletNonce
        WalletNonce.cleanup_expired()
        click.echo('Expired nonces cleaned up.')

    @app.cli.command('process-payouts')
    def process_payouts():
        """Process pending payouts."""
        from app.services.payout_service import process_pending_payouts
        count = process_pending_payouts()
        click.echo(f'Processed {count} payouts.')

    @app.cli.command('make-admin')
    @click.argument('username')
    def make_admin(username):
        """Make a user an admin by username."""
        from app.models import User
        user = User.query.filter_by(username=username).first()
        if not user:
            click.echo(f'User "{username}" not found.')
            return
        user.is_admin = True
        db.session.commit()
        click.echo(f'User "{username}" is now an admin.')

    @app.cli.command('create-admin')
    @click.argument('email')
    @click.argument('username')
    @click.argument('password')
    def create_admin(email, username, password):
        """Create a new admin user."""
        from app.models import User
        if User.query.filter_by(email=email).first():
            click.echo(f'User with email "{email}" already exists.')
            return
        if User.query.filter_by(username=username).first():
            click.echo(f'User with username "{username}" already exists.')
            return
        user = User(
            email=email,
            username=username,
            auth_type='email',
            email_verified=True,
            is_admin=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Admin user "{username}" created successfully.')

    @app.cli.command('seed-categories')
    def seed_categories():
        """Seed default project categories."""
        from app.models import Category
        from app.models.category import DEFAULT_CATEGORIES

        for i, cat_data in enumerate(DEFAULT_CATEGORIES):
            existing = Category.query.filter_by(slug=cat_data['slug']).first()
            if not existing:
                category = Category(
                    name=cat_data['name'],
                    slug=cat_data['slug'],
                    icon=cat_data['icon'],
                    color=cat_data['color'],
                    description=cat_data['description'],
                    sort_order=i
                )
                db.session.add(category)
                click.echo(f'Created category: {cat_data["name"]}')
            else:
                click.echo(f'Category already exists: {cat_data["name"]}')

        db.session.commit()
        click.echo('Categories seeded successfully.')
