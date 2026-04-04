"""
core.invoice — Sequential Invoice Number Generation
------------------------------------------------------
DB-backed, thread-safe via mutex + row-level lock.
"""

import logging
from datetime import datetime

log = logging.getLogger("billedup.generator")


def generate_invoice_number(shop_id: str, is_return: bool = False) -> str:
    """
    Generate next sequential invoice number.
    Stored in DB via SQLAlchemy — survives server restarts and redeploys.
    Thread-safe via mutex + row-level lock.

    is_return=True → prefix "CN" (Credit Note) instead of BILL_PREFIX.
    Credit notes use a separate sequence key to avoid gaps in invoice numbering.
    """
    if not shop_id.strip():
        raise ValueError("shop_id cannot be empty")

    from database import generate_next_sequence

    shop_key = shop_id.upper().strip()
    year     = datetime.now().strftime("%Y")

    if is_return:
        prefix = "CN"
        seq_key = f"CN_{shop_key}"
    else:
        from config import BILL_PREFIX
        prefix = BILL_PREFIX
        seq_key = shop_key

    sequence = generate_next_sequence(seq_key, year)
    invoice_no = f"{prefix}-{year}-{shop_key}-{sequence:05d}"
    log.info(f"Generated {'credit note' if is_return else 'invoice'}: {invoice_no}")
    return invoice_no
