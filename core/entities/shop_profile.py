"""
core.entities.shop_profile — Shop identity and GSTIN handling
"""

import re
from dataclasses import dataclass

VALID_GST_SLABS  = {0, 3, 5, 12, 18, 28}
GSTIN_REGEX      = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
PLACEHOLDER_GSTIN = "GSTIN00000000000"


@dataclass
class ShopProfile:
    shop_id:    str
    name:       str
    address:    str
    gstin:      str
    phone:      str
    state:      str = "Telangana"
    state_code: str = "36"
    upi:        str = ""

    @property
    def has_gstin(self) -> bool:
        """True if shop has a real, valid-format GSTIN (not placeholder)."""
        if not self.gstin or self.gstin == PLACEHOLDER_GSTIN:
            return False
        return bool(GSTIN_REGEX.match(self.gstin.upper().strip()))

    @property
    def display_gstin(self) -> str:
        """GSTIN to show on bill."""
        return self.gstin.upper() if self.has_gstin else "Not Registered"

    @property
    def invoice_type(self) -> str:
        """TAX INVOICE if GSTIN registered, else BILL OF SUPPLY."""
        return "TAX INVOICE" if self.has_gstin else "BILL OF SUPPLY"

    def validate(self):
        if not self.name.strip():
            raise ValueError("Shop name cannot be empty")
        if not self.address.strip():
            raise ValueError("Shop address cannot be empty")
        if self.has_gstin:
            if not GSTIN_REGEX.match(self.gstin.upper().strip()):
                raise ValueError(
                    f"Invalid GSTIN format: '{self.gstin}'. "
                    f"Expected: 22AAAAA0000A1Z5"
                )
        if len(re.sub(r"\D", "", self.phone)) < 10:
            raise ValueError(f"Invalid phone number: '{self.phone}'")
