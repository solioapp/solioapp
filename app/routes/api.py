"""General API routes."""
from flask import Blueprint, jsonify, current_app, request
from flask_login import login_required

from app.extensions import limiter
from app.services.price_service import get_sol_price
from app.models import Category

api_bp = Blueprint('api', __name__)


@api_bp.route('/sol-price')
@limiter.limit("60 per minute")
def sol_price():
    """Get current SOL/USD price."""
    price = get_sol_price()
    return jsonify({
        'price_usd': price,
        'currency': 'USD'
    })


@api_bp.route('/platform-info')
@limiter.exempt
def platform_info():
    """Get platform configuration info."""
    use_devnet = current_app.config.get('USE_DEVNET', True)

    # Get appropriate RPC URL
    if use_devnet:
        rpc_url = current_app.config.get('SOLANA_DEVNET_RPC_URL', 'https://api.devnet.solana.com')
    else:
        rpc_url = current_app.config.get('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')

    return jsonify({
        'name': 'Solio',
        'platform_fee_percent': current_app.config.get('PLATFORM_FEE_PERCENT', 2.5),
        'platform_wallet': current_app.config.get('PLATFORM_WALLET_ADDRESS', ''),
        'use_devnet': use_devnet,
        'rpc_url': rpc_url
    })


@api_bp.route('/health')
@limiter.exempt
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


@api_bp.route('/upload-image', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def upload_image():
    """Upload image for WYSIWYG editor."""
    from app.services.storage_service import upload_image as storage_upload

    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400

    # Check file size (5MB max)
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > 5 * 1024 * 1024:
        return jsonify({'error': 'Image must be smaller than 5MB'}), 400

    # Check file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'error': 'Invalid image format'}), 400

    try:
        image_url = storage_upload(file, folder='editor')
        return jsonify({'success': True, 'url': image_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/categories')
@limiter.exempt
def categories():
    """Get all project categories."""
    cats = Category.query.order_by(Category.sort_order).all()
    return jsonify({
        'categories': [c.to_dict() for c in cats]
    })
