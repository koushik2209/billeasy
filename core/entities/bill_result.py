"""
core.entities.bill_result — Computed bill totals
"""

from dataclasses import dataclass


@dataclass
class BillResult:
    items:       list
    subtotal:    float
    total_cgst:  float
    total_sgst:  float
    total_igst:  float
    total_gst:   float
    grand_total: float
    in_words:    str
    is_igst:     bool = False
