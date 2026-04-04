"""
ai.regex_parser — Rule-Based Fallback Parser
-----------------------------------------------
Used when Claude API fails or returns invalid JSON.
Extracts items from shopkeeper messages using regex patterns.
"""

import re
import logging

from ai.sanitizer import (
    MAX_ITEMS_PER_BILL, MAX_PRICE, MAX_QTY, MIN_PRICE,
    _fix_unit_quantities,
)

log = logging.getLogger("billedup.parser")


def _regex_parse_message(message: str) -> dict:
    """
    Rule-based fallback parser used when Claude API fails or returns
    an invalid/unparseable response.

    Supported patterns (case-insensitive):
      • "item price"          — e.g. "rice 50", "soap 25.5"
      • "item-price"          — e.g. "shirt-500", "pen-12"
      • "item x<qty> price"   — e.g. "rice x3 150", "pen x2 24"
      • "item <qty>x price"   — e.g. "rice 3x 150"
      • "<qty> item price"    — e.g. "3 rice 150"

    Returns the same JSON dict structure as Claude's output.
    """
    log.info("Using regex fallback parser")

    # ── Try to extract customer name from common prefixes ──
    customer_name = "Customer"
    # Stop the name at: comma/newline, end-of-string, OR the start of
    # an "word  number" sequence (which signals the first item).
    customer_pat = re.compile(
        r"(?:bill\s+(?:for|to)|for|to)\s+([A-Za-z][A-Za-z\s]{0,29}?)(?=[,\n]|\s+[A-Za-z]+\s+\d|$)",
        re.IGNORECASE,
    )
    cm = customer_pat.search(message)
    if cm:
        candidate = cm.group(1).strip()
        if len(candidate) >= 2:
            customer_name = candidate.title()
            # Strip the "bill for Name" prefix so name doesn't leak into first item
            message = message[:cm.start()] + message[cm.end():]
            message = message.strip()

    # ── Normalize symbols: @ and = to spaces so "shirt @ 500" works ──
    message = re.sub(r'\s*[@=]\s*', ' ', message)

    items: list[dict] = []
    notes_parts: list[str] = []

    # ── Item extraction patterns (ordered most-specific → least-specific) ──
    patterns = [
        # "item <num><unit> price" — e.g. "gold 500gm 100000", "oil 1kg 120"
        (
            re.compile(
                r"([A-Za-z][A-Za-z\s]{0,30}?)\s+"
                r"(\d+(?:\.\d+)?\s*(?:gm|gms|g|kg|kgs|ml|l|ltr|ltrs|litre|litres|gram|grams))\s+"
                r"(\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "name_unit_price",
        ),
        # "item price x<qty>"  — e.g. "pen 10 x 5", "pen 10 x5", "pen 10 × 5"
        (
            re.compile(
                r"([A-Za-z][A-Za-z\s]{0,30}?)\s+(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "name_price_xqty",
        ),
        # "item x<qty> price"  or  "item <qty>x price"
        (
            re.compile(
                r"([A-Za-z][A-Za-z\s]{0,30}?)\s+[xX](\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "name_xqty_price",
        ),
        (
            re.compile(
                r"([A-Za-z][A-Za-z\s]{0,30}?)\s+(\d+(?:\.\d+)?)[xX]\s+(\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "name_qtyx_price",
        ),
        # "<qty> item price"  — e.g. "3 rice 150"
        (
            re.compile(
                r"(?:^|[,\n]|(?<=\d\s))\s*(\d+(?:\.\d+)?)\s+([A-Za-z][A-Za-z\s]{0,30}?)\s+(\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "qty_name_price",
        ),
        # "item <small-qty> price" — e.g. "charger 2 499", "pen 3 50"
        (
            re.compile(
                r"([A-Za-z][A-Za-z\s]{0,30}?)\s+([2-9])\s+(\d{2,}(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "name_smallqty_price",
        ),
        # "item-price"  — e.g. "shirt-500"
        (
            re.compile(
                r"([A-Za-z][A-Za-z\s]{0,29}?)\s*-\s*(\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "name_dash_price",
        ),
        # "item price"  — e.g. "soap 25"
        (
            re.compile(
                r"([A-Za-z][A-Za-z\s]{0,29}?)\s+(\d+(?:\.\d+)?)",
                re.IGNORECASE,
            ),
            "name_price",
        ),
        # "itemprice" (no space)  — e.g. "shirt99", "pant700"
        (
            re.compile(
                r"([A-Za-z]{2,}[A-Za-z\s]*)(\d{2,6})",
                re.IGNORECASE,
            ),
            "name_nospace_price",
        ),
    ]

    # Track character spans already consumed so patterns don't double-match
    used_spans: list[tuple[int, int]] = []

    def _overlaps(span: tuple[int, int]) -> bool:
        for s, e in used_spans:
            if span[0] < e and span[1] > s:
                return True
        return False

    # Words that should never be treated as item names
    STOPWORDS = {
        "bill", "for", "to", "and", "the", "please", "kindly",
        "rs", "inr", "rupees", "total", "amount", "price", "qty",
        "quantity", "note", "notes", "hi", "hello", "thanks", "thank",
        "dear", "sir", "madam",
    }

    def _clean_name(raw: str) -> str:
        name = raw.strip(" \t-")
        name = re.sub(r"\s+", " ", name)
        # Drop leading/trailing stop-words
        tokens = name.split()
        while tokens and tokens[0].lower() in STOPWORDS:
            tokens = tokens[1:]
        while tokens and tokens[-1].lower() in STOPWORDS:
            tokens = tokens[:-1]
        return " ".join(tokens).strip()

    for pattern, ptype in patterns:
        for m in pattern.finditer(message):
            if _overlaps(m.span()):
                continue

            try:
                if ptype == "name_unit_price":
                    base_name = _clean_name(m.group(1))
                    unit_str  = m.group(2).strip()
                    name  = f"{base_name} {unit_str.lower()}"
                    qty   = 1.0
                    price = float(m.group(3))
                elif ptype == "name_price_xqty":
                    name  = _clean_name(m.group(1))
                    price = float(m.group(2))
                    qty   = float(m.group(3))
                elif ptype == "name_xqty_price":
                    name  = _clean_name(m.group(1))
                    qty   = float(m.group(2))
                    price = float(m.group(3))
                elif ptype == "name_qtyx_price":
                    name  = _clean_name(m.group(1))
                    qty   = float(m.group(2))
                    price = float(m.group(3))
                elif ptype == "qty_name_price":
                    qty   = float(m.group(1))
                    name  = _clean_name(m.group(2))
                    price = float(m.group(3))
                elif ptype == "name_smallqty_price":
                    name  = _clean_name(m.group(1))
                    qty   = float(m.group(2))
                    price = float(m.group(3))
                elif ptype == "name_dash_price":
                    name  = _clean_name(m.group(1))
                    qty   = 1.0
                    price = float(m.group(2))
                elif ptype == "name_nospace_price":
                    name  = _clean_name(m.group(1))
                    qty   = 1.0
                    price = float(m.group(2))
                else:  # name_price
                    name  = _clean_name(m.group(1))
                    qty   = 1.0
                    price = float(m.group(2))
            except (ValueError, IndexError):
                continue

            # Basic sanity checks (mirrors validate_parsed_response limits)
            if not name or name.lower() in STOPWORDS:
                continue
            if 9_000_000_000 <= price <= 9_999_999_999:
                notes_parts.append(f"Skipped possible phone number: {price:.0f}")
                continue
            if price < MIN_PRICE or price > MAX_PRICE:
                continue
            if qty <= 0 or qty > MAX_QTY:
                qty = 1.0

            items.append({
                "name":  name.title(),
                "qty":   round(qty, 3),
                "price": round(price, 2),
            })
            used_spans.append(m.span())

    # De-duplicate items with identical (name, price) that may have been
    # captured by multiple overlapping patterns
    seen: set[tuple] = set()
    unique_items: list[dict] = []
    for it in items:
        key = (it["name"].lower(), it["price"])
        if key not in seen:
            seen.add(key)
            unique_items.append(it)

    # Fix unit quantities: "gold 500gm 100000" should not treat 500 as qty
    unique_items = _fix_unit_quantities(unique_items, message)

    notes_parts.insert(0, "Parsed by regex fallback (Claude API unavailable)")

    # Detect ambiguous compact inputs (e.g., "pen10x5", "shirt1002")
    # where the digit boundary between name/price/qty is unclear
    ambiguous_parse = bool(re.search(
        r"[a-zA-Z]\d+[xX×]\d+|[a-zA-Z]\d{4,}",
        message,
    ))

    warnings = []
    if ambiguous_parse and unique_items:
        warnings.append("ambiguous_parse")

    return {
        "customer_name": customer_name,
        "items":         unique_items[:MAX_ITEMS_PER_BILL],
        "confidence":    0.6 if unique_items else 0.0,
        "notes":         "; ".join(notes_parts),
        "error":         None if unique_items else "No items found by fallback parser",
        "warnings":      warnings,
        "parse_time_ms": 0,
    }
