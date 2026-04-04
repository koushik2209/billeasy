"""
core.entities.customer_info — Customer details for a bill
"""

from dataclasses import dataclass

from core.entities.shop_profile import GSTIN_REGEX


@dataclass
class CustomerInfo:
    name:       str
    phone:      str = ""
    address:    str = ""
    gstin:      str = ""
    state:      str = ""
    state_code: str = ""

    def validate(self):
        if not self.name.strip():
            raise ValueError("Customer name cannot be empty")
        if self.gstin and not GSTIN_REGEX.match(self.gstin.upper().strip()):
            raise ValueError(f"Invalid customer GSTIN: '{self.gstin}'")
