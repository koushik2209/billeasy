"""
reports.py — Backward-Compatible Re-Export Shim
-------------------------------------------------
All code has moved to:
    core/reports.py          — GSTReport, queries, date parsing, formatting
    services/pdf_renderer.py — export_gst_report_pdf
"""

from core.reports import (
    GSTReport,
    get_gst_report,
    parse_report_range,
    format_indian_number,
    msg_gst_report,
    MONTH_NAMES,
)

from services.pdf_renderer import export_gst_report_pdf
