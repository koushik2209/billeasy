"""
db — BilledUp Database Package
-------------------------------
Re-exports all public symbols for convenient imports:
    from db import db_session, Shop, Bill, init_database, ...
"""

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

from db.crud import (
    generate_api_key,
    assign_api_key,
    validate_api_key,
)

from db.item_master import (
    get_item_master,
    save_item_master,
    get_top_items,
    update_item_gst,
)

from db.dedup import (
    try_claim_message,
    maybe_cleanup_processed_messages,
)
