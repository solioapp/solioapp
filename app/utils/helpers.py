"""Helper utilities."""
from datetime import datetime, timedelta
import hashlib
import secrets


def generate_token(length=32):
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def time_ago(dt):
    """Convert datetime to human-readable 'time ago' string."""
    if not dt:
        return ''

    now = datetime.utcnow()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} min ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hours ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} days ago'
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f'{weeks} weeks ago'
    else:
        return dt.strftime('%Y-%m-%d')


def time_remaining(end_date):
    """Get human-readable time remaining."""
    if not end_date:
        return ''

    now = datetime.utcnow()
    diff = end_date - now

    if diff.total_seconds() <= 0:
        return 'Ended'

    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60

    if days > 0:
        return f'{days} days {hours} hrs'
    elif hours > 0:
        return f'{hours} hrs {minutes} min'
    else:
        return f'{minutes} min'


def format_sol(amount):
    """Format SOL amount for display."""
    if amount is None:
        return '0'

    amount = float(amount)

    if amount >= 1:
        return f'{amount:,.2f}'
    elif amount >= 0.01:
        return f'{amount:.4f}'
    else:
        return f'{amount:.9f}'.rstrip('0').rstrip('.')


def truncate_wallet(address, chars=4):
    """Truncate wallet address for display."""
    if not address or len(address) < chars * 2:
        return address
    return f'{address[:chars]}...{address[-chars:]}'


def gravatar_url(email, size=200):
    """Generate Gravatar URL for email."""
    if not email:
        return None
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    return f'https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon'


def parse_video_url(url):
    """Parse video URL and return embed URL."""
    if not url:
        return None

    # YouTube
    youtube_patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
    ]

    import re
    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f'https://www.youtube.com/embed/{video_id}'

    # Vimeo
    vimeo_pattern = r'(?:vimeo\.com/)(\d+)'
    match = re.search(vimeo_pattern, url)
    if match:
        video_id = match.group(1)
        return f'https://player.vimeo.com/video/{video_id}'

    return None
