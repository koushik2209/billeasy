"""
core.reports — GST Report Query, Date Parsing & Formatting
-------------------------------------------------------------
Business logic only. PDF export is in services/pdf_renderer.py.
"""

import re
import logging
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from sqlalchemy import func

from database import db_session, Bill
from config import PLATFORM_NAME

log = logging.getLogger("billedup.reports")


# ════════════════════════════════════════════════
# DATA
# ════════════════════════════════════════════════

@dataclass
class GSTReport:
    shop_id: str
    start_date: date
    end_date: date
    total_invoices: int
    total_sales: float
    total_cgst: float
    total_sgst: float
    total_igst: float
    total_gst: float
    total_returns: float = 0.0
    return_count: int = 0


# ════════════════════════════════════════════════
# QUERY
# ════════════════════════════════════════════════

def get_gst_report(shop_id: str, start_date: date, end_date: date) -> GSTReport:
    """
    Generate GST summary for a shop within a date range.
    Sales and returns are reported separately.
    All amounts rounded to 2 decimal places.
    """
    base_filter = [
        Bill.shop_id == shop_id.upper(),
        func.date(Bill.created_at) >= start_date,
        func.date(Bill.created_at) <= end_date,
    ]

    with db_session() as session:
        # Sales (positive bills)
        sales_row = session.query(
            func.count(Bill.id).label("count"),
            func.coalesce(func.sum(Bill.grand_total), 0).label("total_sales"),
            func.coalesce(func.sum(Bill.total_cgst), 0).label("total_cgst"),
            func.coalesce(func.sum(Bill.total_sgst), 0).label("total_sgst"),
            func.coalesce(func.sum(Bill.total_igst), 0).label("total_igst"),
            func.coalesce(func.sum(Bill.total_gst), 0).label("total_gst"),
        ).filter(*base_filter, Bill.is_return.is_(False)).first()

        # Returns (credit notes)
        return_row = session.query(
            func.count(Bill.id).label("count"),
            func.coalesce(func.sum(Bill.grand_total), 0).label("total_returns"),
        ).filter(*base_filter, Bill.is_return.is_(True)).first()

    total_invoices = (sales_row.count or 0) + (return_row.count or 0)

    return GSTReport(
        shop_id=shop_id.upper(),
        start_date=start_date,
        end_date=end_date,
        total_invoices=total_invoices,
        total_sales=round(float(sales_row.total_sales or 0), 2),
        total_cgst=round(float(sales_row.total_cgst or 0), 2),
        total_sgst=round(float(sales_row.total_sgst or 0), 2),
        total_igst=round(float(sales_row.total_igst or 0), 2),
        total_gst=round(float(sales_row.total_gst or 0), 2),
        total_returns=round(float(return_row.total_returns or 0), 2),
        return_count=return_row.count or 0,
    )


# ════════════════════════════════════════════════
# DATE RANGE PARSING
# ════════════════════════════════════════════════

MONTH_NAMES = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


def parse_report_range(text: str) -> tuple[date, date, str]:
    """
    Parse a date range from user text following 'gst report'.

    Returns (start_date, end_date, label).

    Supported patterns:
        ''                    → current month
        'last 7 days'         → last 7 days
        'last 30 days'        → last 30 days
        'march'               → March of current year
        'march 2026'          → March 2026
        'this month'          → current month
        'last month'          → previous month
    """
    text = text.strip().lower()
    today = date.today()

    # Empty or "this month" → current month
    if not text or text == "this month":
        start = today.replace(day=1)
        label = today.strftime("%B %Y")
        return start, today, label

    # "last month"
    if text == "last month":
        first_of_current = today.replace(day=1)
        end = first_of_current - timedelta(days=1)
        start = end.replace(day=1)
        label = start.strftime("%B %Y")
        return start, end, label

    # "last N days"
    m = re.match(r"last\s+(\d+)\s+days?", text)
    if m:
        n = int(m.group(1))
        n = min(n, 365)  # cap at 1 year
        start = today - timedelta(days=n)
        label = f"Last {n} days"
        return start, today, label

    # "march" or "march 2026"
    m = re.match(r"([a-z]+)(?:\s+(\d{4}))?$", text)
    if m and m.group(1) in MONTH_NAMES:
        month = MONTH_NAMES[m.group(1)]
        year = int(m.group(2)) if m.group(2) else today.year
        start = date(year, month, 1)
        # End of month
        if month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        # Don't go past today
        if end > today:
            end = today
        label = start.strftime("%B %Y")
        return start, end, label

    # Fallback → current month
    start = today.replace(day=1)
    label = today.strftime("%B %Y")
    return start, today, label


# ════════════════════════════════════════════════
# INDIAN NUMBER FORMATTING
# ════════════════════════════════════════════════

def format_indian_number(amount: float) -> str:
    """
    Format a number in Indian lakh/crore style.
    1234567.89 → '12,34,567.89'
    """
    if amount < 0:
        return "-" + format_indian_number(-amount)

    int_part = int(amount)
    dec_part = round(amount - int_part, 2)
    dec_str = f"{dec_part:.2f}"[1:]  # ".89"

    s = str(int_part)
    if len(s) <= 3:
        return s + dec_str

    # Last 3 digits, then groups of 2
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    return result + dec_str


# ════════════════════════════════════════════════
# WHATSAPP MESSAGE FORMAT
# ════════════════════════════════════════════════

def msg_gst_report(report: GSTReport, label: str) -> str:
    """Format GST report for WhatsApp display."""
    if report.total_invoices == 0:
        return (
            f"\U0001f4ca *GST Report ({label})*\n\n"
            f"No invoices found for this period.\n\n"
            f"_{PLATFORM_NAME}_"
        )

    lines = [
        f"\U0001f4ca *GST Report ({label})*\n",
        f"\U0001f9fe Total Invoices: {report.total_invoices}",
        f"\U0001f4b0 Total Sales: Rs.{format_indian_number(report.total_sales)}",
    ]
    if report.return_count > 0:
        lines.append(f"\U0001f501 Returns ({report.return_count}): Rs.{format_indian_number(abs(report.total_returns))}")
        net = report.total_sales + report.total_returns  # returns are negative
        lines.append(f"\U0001f4ca *Net Sales: Rs.{format_indian_number(net)}*")
    lines += [
        "",
        f"\U0001f9fe *GST Breakdown:*",
    ]
    if report.total_cgst or report.total_sgst:
        lines.append(f"  \u2022 CGST: Rs.{format_indian_number(report.total_cgst)}")
        lines.append(f"  \u2022 SGST: Rs.{format_indian_number(report.total_sgst)}")
    if report.total_igst:
        lines.append(f"  \u2022 IGST: Rs.{format_indian_number(report.total_igst)}")
    if not (report.total_cgst or report.total_sgst or report.total_igst):
        lines.append(f"  \u2022 CGST: Rs.0.00")
        lines.append(f"  \u2022 SGST: Rs.0.00")

    lines += [
        f"\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501",
        f"\U0001f4b8 *Total GST: Rs.{format_indian_number(report.total_gst)}*",
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n",
        f"\U0001f4c5 {report.start_date.strftime('%d %b %Y')} \u2014 {report.end_date.strftime('%d %b %Y')}",
        f"\n_{PLATFORM_NAME}_",
    ]
    return "\n".join(lines)
