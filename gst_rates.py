"""
gst_rates.py — Backward-Compatible Re-Export Shim
---------------------------------------------------
All code has moved to core/gst_rates.py.

This file re-exports everything so existing imports still work:
    from gst_rates import get_gst_rate, get_gst_rate_smart, ...
"""

from core.gst_rates import (
    GST_RATES,
    CACHE_FILE,
    FUZZY_THRESHOLD,
    fuzzy_match,
    load_cache,
    save_cache,
    get_gst_rate,
    get_gst_rate_smart,
    get_all_categories,
    CLOTHING_KEYWORDS,
    FOOTWEAR_KEYWORDS,
    FABRIC_ALWAYS_5PCT,
    is_clothing_item,
    is_footwear_item,
    adjust_gst_for_price,
)
