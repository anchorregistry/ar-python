# SPDX-License-Identifier: BUSL-1.1
"""Text types for the TEXT artifact type."""

from enum import StrEnum


class TextType(StrEnum):
    """Types of text artifact that can be registered."""

    BLOG = "BLOG"
    BOOK = "BOOK"
    ESSAY = "ESSAY"
    ARTICLE = "ARTICLE"
    WHITEPAPER = "WHITEPAPER"
