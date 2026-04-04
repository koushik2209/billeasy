"""
db.dedup — WhatsApp Webhook Message Deduplication
---------------------------------------------------
INSERT-FIRST pattern: attempt INSERT, catch IntegrityError for duplicates.
"""

import logging
import threading
from datetime import datetime

from db.models import ProcessedMessage
from db.session import SessionLocal, db_session

log = logging.getLogger("billedup.db")


def try_claim_message(message_id: str) -> bool:
    """INSERT-FIRST dedup: attempt to insert message_id into DB.

    Returns True  → message is NEW, caller should process it.
    Returns False → message is a DUPLICATE, caller should skip.

    Relies on UNIQUE constraint — no check-then-insert race condition.
    On non-integrity DB errors, returns True (fails open: process rather than drop).

    Uses a raw session (not db_session()) to avoid noisy ERROR logs for
    the expected IntegrityError on duplicates.
    """
    session = SessionLocal()
    try:
        session.add(ProcessedMessage(message_id=message_id))
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        err_str = str(e).lower()
        if "unique" in err_str or "duplicate" in err_str or "integrity" in err_str:
            log.debug(f"[DEDUP] Duplicate claim for {message_id}")
            return False
        log.error(f"[DEDUP] Claim DB error for {message_id}: {e}")
        return True
    finally:
        session.close()


_DEDUP_RETENTION_HOURS = 48
_DEDUP_CLEANUP_INTERVAL = 100
_dedup_call_counter = 0
_dedup_counter_lock = threading.Lock()


def maybe_cleanup_processed_messages():
    """Run cleanup only once every _DEDUP_CLEANUP_INTERVAL webhook calls.
    Thread-safe counter — no external cron needed."""
    global _dedup_call_counter
    with _dedup_counter_lock:
        _dedup_call_counter += 1
        if _dedup_call_counter < _DEDUP_CLEANUP_INTERVAL:
            return
        _dedup_call_counter = 0

    try:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=_DEDUP_RETENTION_HOURS)
        with db_session() as session:
            deleted = session.query(ProcessedMessage).filter(
                ProcessedMessage.created_at < cutoff,
            ).delete()
            if deleted:
                log.info(f"[DEDUP] Cleanup: removed {deleted} old records")
    except Exception as e:
        log.warning(f"[DEDUP] Cleanup failed: {e}")
