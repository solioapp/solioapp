"""Donation routes."""
from decimal import Decimal

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from app.extensions import db, limiter
from app.models import Project, Donation, RewardTier
from app.services.solana_service import verify_transaction
from app.services.notification_service import notify_new_donation, notify_milestone_reached
from app.utils.validators import validate_sol_amount

donations_bp = Blueprint('donations', __name__)


@donations_bp.route('/verify', methods=['POST'])
@limiter.limit("30 per minute")
def verify_donation():
    """
    Verify a donation transaction on Solana blockchain.

    Expected JSON payload:
    {
        "project_id": 1,
        "tx_signature": "...",
        "amount_sol": "1.5",
        "donor_wallet": "...",
        "message": "optional message",
        "reward_tier_id": null or tier_id,
        "donor_email": "optional email for reward delivery"
    }
    """
    data = request.get_json()

    project_id = data.get('project_id')
    tx_signature = data.get('tx_signature', '').strip()
    amount_sol = data.get('amount_sol', '')
    donor_wallet = data.get('donor_wallet', '').strip()
    message = data.get('message', '').strip()
    reward_tier_id = data.get('reward_tier_id')
    donor_email = data.get('donor_email', '').strip() if data.get('donor_email') else None

    # Validation
    if not all([project_id, tx_signature, amount_sol, donor_wallet]):
        return jsonify({'error': 'Missing required data'}), 400

    if not validate_sol_amount(amount_sol):
        return jsonify({'error': 'Invalid amount'}), 400

    # Check project exists and is active
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    if not project.is_active:
        return jsonify({'error': 'Project no longer accepts donations'}), 400

    # Check for duplicate transaction
    existing = Donation.query.filter_by(tx_signature=tx_signature).first()
    if existing:
        return jsonify({'error': 'Transaction already processed'}), 400

    # Verify transaction on blockchain
    platform_wallet = current_app.config['PLATFORM_WALLET_ADDRESS']

    verification_result = verify_transaction(
        tx_signature=tx_signature,
        expected_recipient=platform_wallet,
        expected_amount_sol=Decimal(str(amount_sol)),
        expected_sender=donor_wallet
    )

    if not verification_result['success']:
        return jsonify({
            'error': verification_result.get('error', 'Transaction verification failed')
        }), 400

    # Validate and process reward tier if provided
    reward_tier = None
    if reward_tier_id:
        reward_tier = RewardTier.query.get(reward_tier_id)
        if not reward_tier or reward_tier.project_id != project_id:
            return jsonify({'error': 'Invalid reward tier'}), 400
        if not reward_tier.is_available:
            return jsonify({'error': 'This reward tier is sold out'}), 400
        if Decimal(str(amount_sol)) < reward_tier.min_amount_sol:
            return jsonify({'error': f'Minimum amount for this reward is {reward_tier.min_amount_sol} SOL'}), 400
        if not donor_email:
            return jsonify({'error': 'Email is required for reward delivery'}), 400

    # Create donation record
    donation = Donation(
        project_id=project_id,
        user_id=current_user.id if current_user.is_authenticated else None,
        reward_tier_id=reward_tier_id if reward_tier else None,
        amount_sol=Decimal(str(amount_sol)),
        message=message[:1000] if message else None,  # Limit message length
        donor_email=donor_email,
        tx_signature=tx_signature,
        donor_wallet=donor_wallet,
        status='confirmed'
    )
    donation.calculate_fee(current_app.config['PLATFORM_FEE_PERCENT'])

    db.session.add(donation)

    # Update reward tier claimed count if applicable
    if reward_tier:
        reward_tier.claim()

    # Update project raised amount
    project.raised_sol = (project.raised_sol or Decimal('0')) + donation.amount_sol

    # Check and update milestones
    newly_reached_milestones = []
    for milestone in project.milestones:
        if not milestone.reached and project.raised_sol >= milestone.amount_sol:
            milestone.reached = True
            from datetime import datetime
            milestone.reached_at = datetime.utcnow()
            newly_reached_milestones.append(milestone)

    db.session.commit()

    # Send notifications (after commit)
    try:
        notify_new_donation(donation)
        for milestone in newly_reached_milestones:
            notify_milestone_reached(project, milestone)
    except Exception as e:
        # Don't fail the donation if notification fails
        current_app.logger.error(f'Notification error: {e}')

    return jsonify({
        'success': True,
        'donation': donation.to_dict(),
        'project': {
            'raised_sol': str(project.raised_sol),
            'progress_percent': project.progress_percent,
            'donation_count': project.donation_count
        }
    })


@donations_bp.route('/my')
@login_required
def my_donations():
    """Get current user's donations."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    pagination = current_user.donations.filter_by(status='confirmed').order_by(
        Donation.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    if request.is_json or request.args.get('format') == 'json':
        return jsonify({
            'donations': [d.to_dict() for d in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })

    return render_template(
        'profile/my_donations.html',
        donations=pagination.items,
        pagination=pagination
    )


@donations_bp.route('/project/<int:project_id>')
def project_donations(project_id):
    """Get donations for a specific project."""
    project = Project.query.get_or_404(project_id)

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)

    pagination = project.donations.filter_by(status='confirmed').order_by(
        Donation.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'donations': [d.to_dict() for d in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@donations_bp.route('/stats')
def donation_stats():
    """Get platform donation statistics."""
    from sqlalchemy import func

    total_donations = db.session.query(func.count(Donation.id)).filter(
        Donation.status == 'confirmed'
    ).scalar()

    total_raised = db.session.query(func.sum(Donation.amount_sol)).filter(
        Donation.status == 'confirmed'
    ).scalar() or Decimal('0')

    total_projects = db.session.query(func.count(Project.id)).filter(
        Project.status.in_(['active', 'ended'])
    ).scalar()

    return jsonify({
        'total_donations': total_donations,
        'total_raised_sol': str(total_raised),
        'total_projects': total_projects
    })
