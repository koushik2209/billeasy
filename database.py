"""
database.py — Backward-Compatible Re-Export Shim
--------------------------------------------------
All code has moved to the db/ package:
    db/models.py       — SQLAlchemy ORM models
    db/session.py      — Engine, SessionLocal, db_session, init, schema validation
    db/crud.py         — API key management
    db/item_master.py  — Per-shop item GST rate memory
    db/dedup.py        — WhatsApp webhook message dedup

This file re-exports everything so existing imports still work:
    from database import db_session, Shop, Bill, ...
"""

# Models
from db.models import (
    Base,
    Shop,
    Bill,
    SessionRecord,
    InvoiceSequence,
    Registration,
    ConversationLog,
    PendingBillRecord,
    ReportPDF,
    ProcessedMessage,
    ShopItemMaster,
)

# Session, engine, init, schema
from db.session import (
    engine,
    SessionLocal,
    db_session,
    init_database,
    generate_next_sequence,
    validate_schema,
    reset_database,
    ensure_schema,
)

# API key management
from db.crud import (
    generate_api_key,
    assign_api_key,
    validate_api_key,
)

# Item master
from db.item_master import (
    get_item_master,
    save_item_master,
    get_top_items,
    update_item_gst,
)

# Dedup
from db.dedup import (
    try_claim_message,
    maybe_cleanup_processed_messages,
    _DEDUP_RETENTION_HOURS,
    _DEDUP_CLEANUP_INTERVAL,
    _dedup_call_counter,
    _dedup_counter_lock,
)
