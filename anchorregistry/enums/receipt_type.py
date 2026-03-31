# SPDX-License-Identifier: BUSL-1.1
"""Receipt types for the RECEIPT artifact type."""

from enum import StrEnum


class ReceiptType(StrEnum):
    """Types of receipt that can be registered."""

    COMMERCIAL = "COMMERCIAL"
    MEDICAL = "MEDICAL"
    FINANCIAL = "FINANCIAL"
    GOVERNMENT = "GOVERNMENT"
    EVENT = "EVENT"
    SERVICE = "SERVICE"
