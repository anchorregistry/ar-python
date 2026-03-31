# SPDX-License-Identifier: BUSL-1.1
"""Unit tests for decoder.py — raw log → two-level record."""

import pytest


class TestDecodeEvent:
    """Tests for _decode_event()."""

    def test_decodes_code_anchor(self):
        ...

    def test_decodes_research_anchor(self):
        ...

    def test_decodes_all_artifact_types(self):
        ...


class TestDecodeDataFields:
    """Tests for _decode_data_fields()."""

    def test_code_fields(self):
        ...

    def test_account_capacity_uint256(self):
        ...

    def test_unknown_type_raises(self):
        ...
