# SPDX-License-Identifier: BUSL-1.1
"""Entity types for the ENTITY artifact type."""

from enum import StrEnum


class EntityType(StrEnum):
    """Types of entity that can be registered."""

    PERSON = "PERSON"
    COMPANY = "COMPANY"
    INSTITUTION = "INSTITUTION"
    GOVERNMENT = "GOVERNMENT"
    AI_SYSTEM = "AI_SYSTEM"
