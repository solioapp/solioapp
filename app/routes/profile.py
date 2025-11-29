"""Profile and dashboard routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Project, Donation
from app.services.storage_service import upload_image
from app.utils.validators import validate_username, validate_url, validate_wallet_address

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with their projects and stats."""
    # User's published projects (not drafts)
    projects = current_user.projects.filter_by(is_draft=False).order_by(
        Project.created_at.desc()
    ).all()

    # User's draft projects
    draft_projects = current_user.projects.filter_by(is_draft=True).order_by(
        Project.created_at.desc()
    ).all()

    # User's recent donations
    recent_donations = current_user.donations.filter_by(status='confirmed').order_by(
        Donation.created_at.desc()
    ).limit(10).all()

    # Stats (only count published projects)
    total_raised = sum(
        p.raised_sol for p in projects if p.raised_sol
    )
    total_donated = sum(
        d.amount_sol for d in current_user.donations.filter_by(status='confirmed').all()
    )

    return render_template(
        'profile/dashboard.html',
        projects=projects,
        draft_projects=draft_projects,
        recent_donations=recent_donations,
        total_raised=total_raised,
        total_donated=total_donated
    )


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Edit user profile."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        bio = request.form.get('bio', '').strip()
        wallet_address = request.form.get('wallet_address', '').strip()
        twitter_url = request.form.get('twitter_url', '').strip()
        telegram_url = request.form.get('telegram_url', '').strip()
        discord_url = request.form.get('discord_url', '').strip()
        website_url = request.form.get('website_url', '').strip()
        github_url = request.form.get('github_url', '').strip()
        linkedin_url = request.form.get('linkedin_url', '').strip()
        youtube_url = request.form.get('youtube_url', '').strip()

        errors = []

        # Validate username
        if username != current_user.username:
            if not validate_username(username):
                errors.append('Invalid username.')
            elif User.query.filter_by(username=username).first():
                errors.append('Username is already taken.')

        # Validate wallet address
        if wallet_address and not validate_wallet_address(wallet_address):
            errors.append('Invalid Solana address.')

        # Validate URLs
        if twitter_url and not validate_url(twitter_url):
            errors.append('Invalid Twitter URL.')
        if telegram_url and not validate_url(telegram_url):
            errors.append('Invalid Telegram URL.')
        if discord_url and not validate_url(discord_url):
            errors.append('Invalid Discord URL.')
        if website_url and not validate_url(website_url):
            errors.append('Invalid website URL.')
        if github_url and not validate_url(github_url):
            errors.append('Invalid GitHub URL.')
        if linkedin_url and not validate_url(linkedin_url):
            errors.append('Invalid LinkedIn URL.')
        if youtube_url and not validate_url(youtube_url):
            errors.append('Invalid YouTube URL.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('profile/edit.html')

        # Update profile
        current_user.username = username
        current_user.bio = bio[:250] if bio else None
        current_user.wallet_address = wallet_address or None
        current_user.twitter_url = twitter_url or None
        current_user.telegram_url = telegram_url or None
        current_user.discord_url = discord_url or None
        current_user.website_url = website_url or None
        current_user.github_url = github_url or None
        current_user.linkedin_url = linkedin_url or None
        current_user.youtube_url = youtube_url or None

        db.session.commit()

        flash('Profile has been updated.', 'success')
        return redirect(url_for('profile.dashboard'))

    return render_template('profile/edit.html')


@profile_bp.route('/image', methods=['POST'])
@login_required
def upload_profile_image():
    """Upload profile image."""
    if 'image' not in request.files:
        if request.is_json:
            return jsonify({'error': 'No file'}), 400
        flash('No file.', 'error')
        return redirect(url_for('profile.edit'))

    file = request.files['image']

    if file.filename == '':
        if request.is_json:
            return jsonify({'error': 'No file'}), 400
        flash('No file.', 'error')
        return redirect(url_for('profile.edit'))

    try:
        image_url = upload_image(file, folder=f'profiles/{current_user.id}')
        current_user.profile_image = image_url
        db.session.commit()

        if request.is_json:
            return jsonify({'success': True, 'url': image_url})

        flash('Profile photo uploaded.', 'success')
        return redirect(url_for('profile.edit'))

    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Upload error: {str(e)}', 'error')
        return redirect(url_for('profile.edit'))


@profile_bp.route('/u/<username>')
def public_profile(username):
    """Public user profile."""
    user = User.query.filter_by(username=username).first_or_404()

    # User's public projects (exclude drafts)
    projects = user.projects.filter_by(status='active', is_draft=False).order_by(
        Project.created_at.desc()
    ).all()

    ended_projects = user.projects.filter_by(status='ended', is_draft=False).order_by(
        Project.end_date.desc()
    ).all()

    return render_template(
        'profile/public.html',
        profile_user=user,
        projects=projects,
        ended_projects=ended_projects
    )


# ============== API Endpoints ==============

@profile_bp.route('/api/me')
@login_required
def api_me():
    """Get current user profile."""
    return jsonify(current_user.to_dict(include_private=True))


@profile_bp.route('/api/me', methods=['PUT'])
@login_required
def api_update():
    """Update current user profile."""
    data = request.get_json()

    errors = []

    username = data.get('username', '').strip()
    if username and username != current_user.username:
        if not validate_username(username):
            errors.append('Invalid username.')
        elif User.query.filter_by(username=username).first():
            errors.append('Username is already taken.')
        else:
            current_user.username = username

    wallet_address = data.get('wallet_address', '').strip()
    if wallet_address:
        if not validate_wallet_address(wallet_address):
            errors.append('Invalid Solana address.')
        else:
            current_user.wallet_address = wallet_address
    elif 'wallet_address' in data:
        current_user.wallet_address = None

    if 'bio' in data:
        bio = data['bio'].strip() if data['bio'] else None
        current_user.bio = bio[:250] if bio else None

    # Social links
    for field in ['twitter_url', 'telegram_url', 'discord_url', 'website_url', 'github_url', 'linkedin_url', 'youtube_url']:
        if field in data:
            value = data[field].strip() if data[field] else None
            if value and not validate_url(value):
                errors.append(f'Invalid URL for {field}.')
            else:
                setattr(current_user, field, value)

    if errors:
        return jsonify({'errors': errors}), 400

    db.session.commit()

    return jsonify({
        'success': True,
        'user': current_user.to_dict(include_private=True)
    })


@profile_bp.route('/api/u/<username>')
def api_public_profile(username):
    """Get public user profile."""
    user = User.query.filter_by(username=username).first_or_404()
    return jsonify(user.to_dict())


@profile_bp.route('/api/u/<username>/projects')
def api_user_projects(username):
    """Get user's public projects."""
    user = User.query.filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 12, type=int), 50)

    query = user.projects.filter(
        Project.status.in_(['active', 'ended'])
    ).order_by(Project.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'projects': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })
