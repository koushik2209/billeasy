"""
db.crud — API Key Management
------------------------------
"""

import secrets
import logging

from db.models import Shop
from db.session import db_session

log = logging.getLogger("billedup.db")


def generate_api_key() -> str:
    """Generate a unique 48-char API key prefixed with 'bu_'."""
    return "bu_" + secrets.token_hex(24)


def assign_api_key(shop_id: str) -> str:
    """Generate and assign a new API key to a shop. Returns the key."""
    key = generate_api_key()
    with db_session() as session:
        shop = session.query(Shop).filter_by(shop_id=shop_id.upper()).first()
        if not shop:
            raise ValueError(f"Shop '{shop_id}' not found")
        shop.api_key = key
    log.info(f"API key assigned to shop {shop_id}")
    return key


def validate_api_key(api_key: str) -> Shop | None:
    """Validate an API key. Returns the Shop if valid, None otherwise."""
    if not api_key or not api_key.startswith("bu_"):
        return None
    with db_session() as session:
        shop = session.query(Shop).filter_by(api_key=api_key, active=True).first()
        if shop:
            session.expunge(shop)
        return shop
