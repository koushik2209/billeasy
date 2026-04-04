"""
claude_parser.py — Backward-Compatible Re-Export Shim
------------------------------------------------------
All code has moved to:
    ai/sanitizer.py      — sanitize_message, validate_parsed_response, _fix_unit_quantities
    ai/regex_parser.py   — _regex_parse_message (fallback parser)
    ai/parser.py         — parse_message, RateLimiter, Claude API call

This file re-exports everything so existing imports still work:
    from claude_parser import parse_message, sanitize_message, ...
"""

# Sanitizer
from ai.sanitizer import (
    sanitize_message,
    validate_parsed_response,
    _fix_unit_quantities,
    MAX_MESSAGE_LENGTH,
    MAX_ITEMS_PER_BILL,
    MAX_PRICE,
    MAX_QTY,
    MIN_PRICE,
    _UNIT_PATTERN,
)

# Regex fallback parser
from ai.regex_parser import _regex_parse_message

# Claude API parser
from ai.parser import (
    parse_message,
    format_result,
    RateLimiter,
    _error_result,
    _elapsed_ms,
    _rate_limiter,
    SYSTEM_PROMPT,
    MAX_RETRIES,
    RETRY_DELAYS,
    RATE_LIMIT_CALLS,
    RATE_LIMIT_WINDOW,
)
