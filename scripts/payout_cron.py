#!/usr/bin/env python
"""
Payout scheduler script.
Runs every 5 minutes to process pending payouts for ended projects.

Run with: python scripts/payout_cron.py
Or set up as a cron job / systemd service.
"""
import os
import sys
import time
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app import create_app
from app.services.payout_service import process_pending_payouts
from app.models import WalletNonce

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = create_app(os.environ.get('FLASK_ENV', 'production'))


def process_payouts_job():
    """Job to process pending payouts."""
    with app.app_context():
        try:
            count = process_pending_payouts()
            if count > 0:
                logger.info(f'Processed {count} payouts')
        except Exception as e:
            logger.error(f'Payout processing error: {e}')


def cleanup_nonces_job():
    """Job to clean up expired wallet nonces."""
    with app.app_context():
        try:
            WalletNonce.cleanup_expired()
            logger.debug('Cleaned up expired nonces')
        except Exception as e:
            logger.error(f'Nonce cleanup error: {e}')


def main():
    """Main entry point."""
    scheduler = BlockingScheduler()

    # Process payouts every 5 minutes
    scheduler.add_job(
        process_payouts_job,
        IntervalTrigger(minutes=5),
        id='process_payouts',
        name='Process pending payouts',
        replace_existing=True
    )

    # Clean up nonces every 15 minutes
    scheduler.add_job(
        cleanup_nonces_job,
        IntervalTrigger(minutes=15),
        id='cleanup_nonces',
        name='Clean up expired nonces',
        replace_existing=True
    )

    logger.info('Payout scheduler started')

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info('Payout scheduler stopped')


if __name__ == '__main__':
    main()
