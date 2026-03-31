# SPDX-License-Identifier: BUSL-1.1
"""Note types for the NOTE artifact type."""

from enum import StrEnum


class NoteType(StrEnum):
    """Types of note that can be registered."""

    MEMO = "MEMO"
    MEETING = "MEETING"
    CORRESPONDENCE = "CORRESPONDENCE"
    OBSERVATION = "OBSERVATION"
    FIELD_NOTE = "FIELD_NOTE"
