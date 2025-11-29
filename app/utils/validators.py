"""Input validation utilities."""
import re
from decimal import Decimal, InvalidOperation


def validate_email(email):
    """Validate email format."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password):
    """Validate password strength."""
    if not password:
        return False
    return len(password) >= 8


def validate_username(username):
    """Validate username format."""
    if not username:
        return False
    # 3-30 characters, alphanumeric and underscores only
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return bool(re.match(pattern, username))


def validate_wallet_address(address):
    """Validate Solana wallet address format."""
    if not address:
        return False
    # Solana addresses are base58 encoded, 32-44 characters
    pattern = r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'
    return bool(re.match(pattern, address))


def validate_sol_amount(amount):
    """Validate SOL amount."""
    try:
        amount = Decimal(str(amount))
        # Must be positive and reasonable (max 1 billion SOL)
        return Decimal('0') < amount <= Decimal('1000000000')
    except (InvalidOperation, ValueError, TypeError):
        return False


def validate_url(url, allowed_schemes=('http', 'https')):
    """Validate URL format."""
    if not url:
        return True  # Empty URLs are valid (optional fields)
    pattern = r'^(https?):\/\/[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url, re.IGNORECASE):
        return False
    # Check scheme
    scheme = url.split('://')[0].lower()
    return scheme in allowed_schemes


def validate_project_title(title):
    """Validate project title."""
    if not title:
        return False
    return 3 <= len(title.strip()) <= 100


def validate_project_description(description):
    """Validate project description."""
    if not description:
        return False
    return 10 <= len(description.strip()) <= 50000


def sanitize_html(html):
    """Sanitize HTML content to prevent XSS."""
    import bleach

    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 's',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'a', 'img',
        'blockquote', 'pre', 'code'
    ]

    allowed_attributes = {
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title', 'width', 'height']
    }

    return bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
