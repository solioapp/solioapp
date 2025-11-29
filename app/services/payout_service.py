"""Payout service for processing creator payments."""
from datetime import datetime
from decimal import Decimal

from flask import current_app

from app.extensions import db
from app.models import Project, Payout
from app.services.solana_service import send_sol, get_transaction_status
from app.services.email_service import send_payout_notification


def process_pending_payouts():
    """
    Process all pending payouts for ended projects.
    Called by scheduler every 5 minutes.

    Returns number of payouts processed.
    """
    processed = 0

    # Find ended projects that need payout
    projects = Project.query.filter(
        Project.status == 'active',
        Project.end_date < datetime.utcnow(),
        Project.payout_status == 'pending',
        Project.raised_sol > 0
    ).all()

    for project in projects:
        # Mark project as ended
        project.status = 'ended'

        # Check if creator has wallet address
        if not project.creator.wallet_address:
            current_app.logger.warning(
                f"Project {project.id} creator has no wallet address"
            )
            continue

        # Create payout record
        success = process_single_payout(project)
        if success:
            processed += 1

    db.session.commit()
    return processed


def process_single_payout(project: Project) -> bool:
    """
    Process payout for a single project.

    Returns True if successful.
    """
    try:
        platform_fee_percent = current_app.config.get('PLATFORM_FEE_PERCENT', 2.5)
        platform_secret = current_app.config.get('PLATFORM_WALLET_SECRET', '')

        if not platform_secret:
            current_app.logger.error("Platform wallet secret not configured")
            return False

        # Calculate amounts
        total_raised = project.raised_sol or Decimal('0')
        platform_fee = total_raised * Decimal(str(platform_fee_percent)) / Decimal('100')
        net_amount = total_raised - platform_fee

        # Minimum payout check (need to cover transaction fee ~0.000005 SOL)
        if net_amount < Decimal('0.001'):
            current_app.logger.warning(
                f"Project {project.id} net amount too small: {net_amount}"
            )
            return False

        # Create payout record
        payout = Payout(
            project_id=project.id,
            total_raised=total_raised,
            platform_fee=platform_fee,
            net_amount=net_amount,
            recipient_wallet=project.creator.wallet_address,
            status='processing'
        )
        db.session.add(payout)
        db.session.flush()

        project.payout_status = 'processing'

        # Send SOL to creator
        result = send_sol(
            recipient=project.creator.wallet_address,
            amount_sol=net_amount,
            sender_secret=platform_secret
        )

        if result['success']:
            payout.tx_signature = result['signature']
            payout.status = 'completed'
            payout.completed_at = datetime.utcnow()
            project.payout_status = 'completed'
            project.payout_tx = result['signature']

            current_app.logger.info(
                f"Payout successful for project {project.id}: {result['signature']}"
            )

            # Send email notification
            try:
                send_payout_notification(project, payout)
            except Exception as e:
                current_app.logger.error(f"Failed to send payout email: {e}")

            return True
        else:
            payout.status = 'failed'
            payout.error_message = result.get('error', 'Unknown error')
            project.payout_status = 'failed'

            current_app.logger.error(
                f"Payout failed for project {project.id}: {result.get('error')}"
            )
            return False

    except Exception as e:
        current_app.logger.error(f"Payout error for project {project.id}: {e}")
        project.payout_status = 'failed'
        return False


def retry_failed_payout(project_id: int) -> dict:
    """
    Retry a failed payout manually.

    Returns dict with success status and message.
    """
    project = Project.query.get(project_id)

    if not project:
        return {'success': False, 'error': 'Project not found'}

    if project.payout_status != 'failed':
        return {'success': False, 'error': 'Payout is not in failed status'}

    if not project.creator.wallet_address:
        return {'success': False, 'error': 'Creator has no wallet address set'}

    # Reset status and try again
    project.payout_status = 'pending'
    db.session.commit()

    success = process_single_payout(project)
    db.session.commit()

    if success:
        return {'success': True, 'message': 'Payout sent successfully'}
    else:
        return {'success': False, 'error': 'Payout failed'}


def get_payout_summary():
    """Get summary of all payouts."""
    from sqlalchemy import func

    total_payouts = db.session.query(func.count(Payout.id)).scalar()

    completed_payouts = db.session.query(func.count(Payout.id)).filter(
        Payout.status == 'completed'
    ).scalar()

    total_paid_out = db.session.query(func.sum(Payout.net_amount)).filter(
        Payout.status == 'completed'
    ).scalar() or Decimal('0')

    total_fees = db.session.query(func.sum(Payout.platform_fee)).filter(
        Payout.status == 'completed'
    ).scalar() or Decimal('0')

    pending_payouts = db.session.query(func.count(Payout.id)).filter(
        Payout.status.in_(['pending', 'processing'])
    ).scalar()

    failed_payouts = db.session.query(func.count(Payout.id)).filter(
        Payout.status == 'failed'
    ).scalar()

    return {
        'total_payouts': total_payouts,
        'completed_payouts': completed_payouts,
        'total_paid_out_sol': str(total_paid_out),
        'total_fees_sol': str(total_fees),
        'pending_payouts': pending_payouts,
        'failed_payouts': failed_payouts
    }
