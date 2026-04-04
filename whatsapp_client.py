"""
whatsapp_client.py — Backward-Compatible Re-Export Shim
--------------------------------------------------------
All code has moved to api/whatsapp_client.py.
"""

from api.whatsapp_client import (
    GRAPH_API_VERSION,
    MAX_RETRIES,
    RETRY_DELAYS,
    digits_only,
    normalize_whatsapp_sender,
    send_text_message,
    send_template_message,
    send_document_by_link,
    parse_meta_webhook_payload,
    send_test_message,
)
