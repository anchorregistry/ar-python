# SPDX-License-Identifier: BUSL-1.1
"""Proof types for the PROOF artifact type."""

from enum import StrEnum


class ProofType(StrEnum):
    """Types of proof that can be registered."""

    ZK = "ZK"
    FORMAL = "FORMAL"
    AUDIT = "AUDIT"
    CRYPTOGRAPHIC = "CRYPTOGRAPHIC"
