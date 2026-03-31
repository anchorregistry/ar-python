# SPDX-License-Identifier: BUSL-1.1
"""ArtifactType enum — 23 types matching the on-chain ArtifactType enum."""

from enum import IntEnum


class ArtifactType(IntEnum):
    """Twenty-three artifact types in eight logical groups."""

    # ── CONTENT (0-11) ────────────────────────────────────────────────
    CODE = 0
    RESEARCH = 1
    DATA = 2
    MODEL = 3
    AGENT = 4
    MEDIA = 5
    TEXT = 6
    POST = 7
    ONCHAIN = 8
    REPORT = 9
    NOTE = 10
    WEBSITE = 11

    # ── LIFECYCLE (12) ────────────────────────────────────────────────
    EVENT = 12

    # ── TRANSACTION (13) ──────────────────────────────────────────────
    RECEIPT = 13

    # ── GATED (14-16) ─────────────────────────────────────────────────
    LEGAL = 14
    ENTITY = 15
    PROOF = 16

    # ── SELF-SERVICE (17) ─────────────────────────────────────────────
    RETRACTION = 17

    # ── REVIEW (18-20) ────────────────────────────────────────────────
    REVIEW = 18
    VOID = 19
    AFFIRMED = 20

    # ── BILLING (21) ──────────────────────────────────────────────────
    ACCOUNT = 21

    # ── CATCH-ALL (22) ────────────────────────────────────────────────
    OTHER = 22
