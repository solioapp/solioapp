"""Price service for SOL/USD conversion."""
import time
from typing import Optional

import requests
from flask import current_app

# Simple in-memory cache
_price_cache = {
    'price': None,
    'timestamp': 0
}


def get_sol_price() -> Optional[float]:
    """
    Get current SOL/USD price.

    Uses CoinGecko API with caching.
    """
    cache_seconds = current_app.config.get('SOL_PRICE_CACHE_SECONDS', 60)

    # Check cache
    if _price_cache['price'] and (time.time() - _price_cache['timestamp']) < cache_seconds:
        return _price_cache['price']

    try:
        response = requests.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={
                'ids': 'solana',
                'vs_currencies': 'usd'
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        price = data.get('solana', {}).get('usd')

        if price:
            _price_cache['price'] = price
            _price_cache['timestamp'] = time.time()
            return price

    except Exception as e:
        current_app.logger.error(f"Price fetch error: {e}")

    # Return cached price even if expired, or None
    return _price_cache['price']


def sol_to_usd(sol_amount: float) -> Optional[float]:
    """Convert SOL amount to USD."""
    price = get_sol_price()
    if price:
        return sol_amount * price
    return None


def usd_to_sol(usd_amount: float) -> Optional[float]:
    """Convert USD amount to SOL."""
    price = get_sol_price()
    if price and price > 0:
        return usd_amount / price
    return None
