"""
bill_generator.py — Backward-Compatible Re-Export Shim
-------------------------------------------------------
All code has moved to:
    core/entities/       — BillItem, ShopProfile, CustomerInfo, BillResult
    core/billing.py      — calculate_bill, is_intra_state, number_to_words
    core/invoice.py      — generate_invoice_number
    services/pdf_renderer.py — generate_pdf_bill, _styles

This file re-exports everything so existing imports still work:
    from bill_generator import ShopProfile, BillItem, generate_pdf_bill, ...
"""

# Entities & constants
from core.entities import (
    BillItem,
    ShopProfile,
    CustomerInfo,
    BillResult,
    GSTIN_REGEX,
    PLACEHOLDER_GSTIN,
    VALID_GST_SLABS,
)

# Calculation logic
from core.billing import (
    calculate_bill,
    is_intra_state,
    number_to_words,
)

# Invoice numbering
from core.invoice import generate_invoice_number

# PDF generation
from services.pdf_renderer import generate_pdf_bill
