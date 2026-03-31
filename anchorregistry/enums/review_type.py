# SPDX-License-Identifier: BUSL-1.1
"""Review types for the REVIEW artifact type."""

from enum import StrEnum


class ReviewType(StrEnum):
    """Types of review that can be registered."""

    PEER_REVIEW = "PEER_REVIEW"
    AUDIT = "AUDIT"
    VERIFICATION = "VERIFICATION"
    ASSESSMENT = "ASSESSMENT"
