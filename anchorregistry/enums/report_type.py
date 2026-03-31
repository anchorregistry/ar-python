# SPDX-License-Identifier: BUSL-1.1
"""Report types for the REPORT artifact type."""

from enum import StrEnum


class ReportType(StrEnum):
    """Types of report that can be registered."""

    CONSULTING = "CONSULTING"
    FINANCIAL = "FINANCIAL"
    COMPLIANCE = "COMPLIANCE"
    ESG = "ESG"
    TECHNICAL = "TECHNICAL"
    AUDIT = "AUDIT"
