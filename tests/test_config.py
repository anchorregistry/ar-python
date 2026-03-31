# SPDX-License-Identifier: BUSL-1.1
"""Tests for configure() and env var resolution."""

import pytest


class TestConfigure:
    """Tests for configure()."""

    def test_sepolia_network(self):
        ...

    def test_base_network(self):
        ...

    def test_invalid_network_raises(self):
        ...

    def test_explicit_overrides_env(self):
        ...


class TestResolveConfig:
    """Tests for _resolve_config()."""

    def test_priority_order(self):
        ...

    def test_no_address_raises(self):
        ...
