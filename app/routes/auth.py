"""Authentication routes."""
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from app.extensions import db, oauth, limiter, csrf
from app.models import User, WalletNonce
from app.services.email_service import send_verification_email, send_password_reset_email
from app.utils.validators import validate_email, validate_password, validate_username

auth_bp = Blueprint('auth', __name__)


# ============== Email Authentication ==============

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register new user with email."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        username = request.form.get('username', '').strip()

        # Validation
        errors = []

        if not validate_email(email):
            errors.append('Invalid email.')

        if not validate_password(password):
            errors.append('Password must be at least 8 characters.')

        if not validate_username(username):
            errors.append('Username must be 3-30 characters and contain only letters, numbers, and underscores.')

        if User.query.filter_by(email=email).first():
            errors.append('Email is already registered.')

        if User.query.filter_by(username=username).first():
            errors.append('Username is already taken.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html', email=email, username=username)

        # Create user (auto-verified, no email confirmation needed)
        user = User(
            email=email,
            username=username,
            auth_type='email',
            email_verified=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Auto-login after registration
        login_user(user)

        flash('Registration successful! Welcome to Solio.', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Login with email."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page if next_page else url_for('main.index'))

        flash('Invalid email or password.', 'error')
        return render_template('auth/login.html', email=email)

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify email address."""
    user = User.query.filter_by(email_verification_token=token).first()

    if not user:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('auth.login'))

    user.email_verified = True
    user.email_verification_token = None
    db.session.commit()

    flash('Email successfully verified! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def forgot_password():
    """Request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        # Always show success message to prevent email enumeration
        flash('If the email exists in our system, you will receive a password reset link.', 'info')

        if user and user.auth_type == 'email':
            # Generate reset token with 30 minute expiry
            user.password_reset_token = secrets.token_urlsafe(32)
            user.password_reset_expires = datetime.utcnow() + timedelta(minutes=30)
            db.session.commit()

            # Send reset email
            send_password_reset_email(user)

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.query.filter_by(password_reset_token=token).first()

    # Check if token is valid and not expired
    if not user or not user.password_reset_expires:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if datetime.utcnow() > user.password_reset_expires:
        # Clear expired token
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        flash('Reset link has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

        if not validate_password(password):
            errors.append('Password must be at least 8 characters.')

        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/reset_password.html', token=token)

        # Update password and clear reset token
        user.set_password(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()

        flash('Password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


# ============== Google OAuth ==============

@auth_bp.route('/google')
def google_login():
    """Initiate Google OAuth login."""
    if not current_app.config.get('GOOGLE_CLIENT_ID'):
        flash('Google login is not configured.', 'error')
        return redirect(url_for('auth.login'))

    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')

        if not user_info:
            flash('Failed to get information from Google.', 'error')
            return redirect(url_for('auth.login'))

        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', '').replace(' ', '_').lower()

        # Check if user exists
        user = User.query.filter_by(google_id=google_id).first()

        if not user:
            # Check if email is already registered
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email is already registered using another method.', 'error')
                return redirect(url_for('auth.login'))

            # Generate unique username
            base_username = name[:20] if name else email.split('@')[0][:20]
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                email=email,
                username=username,
                google_id=google_id,
                auth_type='google',
                email_verified=True,
                profile_image=user_info.get('picture')
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash('Google login successful!', 'success')
        return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(f'Google OAuth error: {e}')
        flash('Error logging in via Google.', 'error')
        return redirect(url_for('auth.login'))


# ============== Twitter/X OAuth ==============

@auth_bp.route('/twitter')
def twitter_login():
    """Initiate Twitter/X OAuth login."""
    if not current_app.config.get('TWITTER_CLIENT_ID'):
        flash('Twitter login is not configured.', 'error')
        return redirect(url_for('auth.login'))

    redirect_uri = url_for('auth.twitter_callback', _external=True)
    return oauth.twitter.authorize_redirect(redirect_uri)


@auth_bp.route('/twitter/callback')
def twitter_callback():
    """Handle Twitter/X OAuth callback."""
    try:
        token = oauth.twitter.authorize_access_token()

        # Get user info from Twitter API
        resp = oauth.twitter.get('users/me', params={'user.fields': 'profile_image_url'})
        user_info = resp.json().get('data', {})

        twitter_id = user_info.get('id')
        username_base = user_info.get('username', '')

        # Check if user exists
        user = User.query.filter_by(twitter_id=twitter_id).first()

        if not user:
            # Generate unique username
            username = username_base[:30] if username_base else f'user_{twitter_id[:8]}'
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{username_base[:25]}{counter}"
                counter += 1

            user = User(
                username=username,
                twitter_id=twitter_id,
                auth_type='twitter',
                email_verified=True,  # No email for Twitter users
                profile_image=user_info.get('profile_image_url', '').replace('_normal', '')
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash('X login successful!', 'success')
        return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(f'Twitter OAuth error: {e}')
        flash('Error logging in via X.', 'error')
        return redirect(url_for('auth.login'))


# ============== Wallet Authentication ==============

@auth_bp.route('/wallet/nonce', methods=['POST'])
@csrf.exempt
@limiter.limit("10 per minute")
def wallet_nonce():
    """Generate nonce for wallet authentication."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400

        wallet_address = data.get('wallet_address', '').strip()

        if not wallet_address or len(wallet_address) != 44:
            return jsonify({'error': 'Invalid wallet address'}), 400

        # Clean up old nonces for this wallet
        WalletNonce.query.filter_by(wallet_address=wallet_address).delete()

        # Generate new nonce
        nonce = WalletNonce.generate(
            wallet_address,
            expiry_minutes=current_app.config.get('WALLET_NONCE_EXPIRY_MINUTES', 10)
        )
        db.session.add(nonce)
        db.session.commit()

        return jsonify({
            'nonce': nonce.nonce,
            'message': nonce.message_to_sign
        })

    except Exception as e:
        current_app.logger.error(f'Wallet nonce error: {e}')
        return jsonify({'error': 'Failed to generate nonce'}), 500


@auth_bp.route('/wallet/verify', methods=['POST'])
@csrf.exempt
@limiter.limit("5 per minute")
def wallet_verify():
    """Verify wallet signature and authenticate user."""
    try:
        from app.services.solana_service import verify_wallet_signature

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400

        wallet_address = data.get('wallet_address', '').strip()
        signature = data.get('signature', '')
        nonce = data.get('nonce', '')

        if not all([wallet_address, signature, nonce]):
            return jsonify({'error': 'Missing required data'}), 400

        # Find and validate nonce
        wallet_nonce = WalletNonce.query.filter_by(
            wallet_address=wallet_address,
            nonce=nonce
        ).first()

        if not wallet_nonce or not wallet_nonce.is_valid:
            return jsonify({'error': 'Invalid or expired nonce'}), 400

        # Verify signature
        message = wallet_nonce.message_to_sign
        if not verify_wallet_signature(wallet_address, message, signature):
            return jsonify({'error': 'Invalid signature'}), 400

        # Mark nonce as used
        wallet_nonce.mark_used()

        # Find or create user
        user = User.query.filter_by(wallet_address=wallet_address).first()

        if not user:
            # Generate unique username from wallet address
            username = f"wallet_{wallet_address[:8]}"
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"wallet_{wallet_address[:6]}{counter}"
                counter += 1

            user = User(
                username=username,
                wallet_address=wallet_address,
                auth_type='wallet',
                email_verified=True  # No email needed for wallet users
            )
            db.session.add(user)

        db.session.commit()

        login_user(user)

        return jsonify({
            'success': True,
            'user': user.to_dict(include_private=True)
        })

    except Exception as e:
        current_app.logger.error(f'Wallet verify error: {e}')
        return jsonify({'error': 'Authentication failed'}), 500


# ============== API Endpoints ==============

@auth_bp.route('/api/register', methods=['POST'])
@limiter.limit("3 per minute")
def api_register():
    """API endpoint for registration."""
    data = request.get_json()

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    username = data.get('username', '').strip()

    errors = []

    if not validate_email(email):
        errors.append('Invalid email.')

    if not validate_password(password):
        errors.append('Password must be at least 8 characters.')

    if not validate_username(username):
        errors.append('Invalid username.')

    if User.query.filter_by(email=email).first():
        errors.append('Email is already registered.')

    if User.query.filter_by(username=username).first():
        errors.append('Username is already taken.')

    if errors:
        return jsonify({'errors': errors}), 400

    user = User(
        email=email,
        username=username,
        auth_type='email',
        email_verified=True
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    login_user(user)

    return jsonify({
        'success': True,
        'message': 'Registration successful.',
        'user': user.to_dict(include_private=True)
    })


@auth_bp.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def api_login():
    """API endpoint for login."""
    data = request.get_json()

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    login_user(user)

    return jsonify({
        'success': True,
        'user': user.to_dict(include_private=True)
    })


@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    """API endpoint for logout."""
    logout_user()
    return jsonify({'success': True})


@auth_bp.route('/api/me')
def api_me():
    """Get current user info."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict(include_private=True)
        })
    return jsonify({'authenticated': False})
