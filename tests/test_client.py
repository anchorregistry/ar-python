# SPDX-License-Identifier: BUSL-1.1
"""Integration tests for client.py — run against Sepolia testnet."""

import os

import pytest

TEST_CONTRACT = "0x9dAb9f5B754f8C56B5F7BAd3E92A8bDe7317AD29"
TEST_RPC = os.environ.get("SEPOLIA_RPC_URL")
TEST_AR_ID = "AR-2026-x1llnO1"


@pytest.fixture(autouse=True)
def _configure_sepolia():
    """Configure the package for Sepolia before each test."""
    ...


class TestGetByArid:
    """Tests for get_by_arid()."""

    def test_returns_valid_record(self):
        ...

    def test_not_found_raises(self):
        ...


class TestGetByRegistrant:
    """Tests for get_by_registrant()."""

    def test_returns_list(self):
        ...


class TestGetByTree:
    """Tests for get_by_tree()."""

    def test_returns_tree_records(self):
        ...


class TestGetByType:
    """Tests for get_by_type()."""

    def test_filters_by_type(self):
        ...


class TestGetAll:
    """Tests for get_all()."""

    def test_returns_all_records(self):
        ...

    def test_block_range(self):
        ...


class TestVerify:
    """Tests for verify()."""

    def test_verify_record_only(self):
        ...

    def test_verify_with_file(self):
        ...


class TestWatermark:
    """Tests for watermark()."""

    def test_code_type_returns_spdx(self):
        ...

    def test_non_code_returns_dapx(self):
        ...
