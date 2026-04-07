# SPDX-License-Identifier: BUSL-1.1
"""ArtifactType enum — 24 types matching the on-chain ArtifactType enum."""

from enum import IntEnum


class ArtifactType(IntEnum):
    """Twenty-four artifact types in eight logical groups."""

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

    # ── SELF-SERVICE (17-18) ──────────────────────────────────────────
    SEAL = 17
    RETRACTION = 18

    # ── REVIEW (19-21) ────────────────────────────────────────────────
    REVIEW = 19
    VOID = 20
    AFFIRMED = 21

    # ── BILLING (22) ──────────────────────────────────────────────────
    ACCOUNT = 22

    # ── CATCH-ALL (23) ────────────────────────────────────────────────
    OTHER = 23
