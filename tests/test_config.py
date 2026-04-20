# SPDX-License-Identifier: BUSL-1.1
"""Tests for configure() and env var resolution."""

import os

import pytest

from anchorregistry.config import _resolve_config, configure
from anchorregistry.constants import NETWORKS
from anchorregistry.exceptions import ConfigurationError


@pytest.fixture(autouse=True)
def _reset_config():
    """Reset config module state before each test."""
    import anchorregistry.config as cfg

    orig_network = cfg._active_network
    orig_address = cfg._explicit_address
    orig_rpc = cfg._explicit_rpc_url
    yield
    cfg._active_network = orig_network
    cfg._explicit_address = orig_address
    cfg._explicit_rpc_url = orig_rpc


class TestConfigure:
    """Tests for configure()."""

    def test_sepolia_network(self, monkeypatch):
        # v0.1.8+ ships no default address per-network; caller must supply it.
        monkeypatch.delenv("ANCHOR_REGISTRY_ADDRESS", raising=False)
        configure(
            network="sepolia",
            contract_address="0xE772B7f4eC4a92109b8b892Add205ede7c850DBa",
            deploy_block=10575629,
        )
        addr, rpc, deploy = _resolve_config()
        assert addr == "0xE772B7f4eC4a92109b8b892Add205ede7c850DBa"
        assert deploy == 10575629

    def test_base_network(self, monkeypatch):
        # Clear BASE_RPC_URL so the assertion against the preset RPC is
        # deterministic under a developer env that has a real provider set.
        monkeypatch.delenv("BASE_RPC_URL", raising=False)
        configure(
            network="base",
            contract_address="0x1234567890abcdef1234567890abcdef12345678",
        )
        addr, rpc, deploy = _resolve_config()
        assert addr == "0x1234567890abcdef1234567890abcdef12345678"
        assert rpc == NETWORKS["base"]["rpc_url"]

    def test_invalid_network_raises(self):
        with pytest.raises(ConfigurationError, match="Unknown network"):
            configure(network="invalid")

    def test_explicit_overrides_env(self, monkeypatch):
        monkeypatch.setenv("ANCHOR_REGISTRY_ADDRESS", "0xENV_ADDR")
        configure(
            network="sepolia",
            contract_address="0xEXPLICIT_ADDR",
            rpc_url="https://explicit-rpc.com",
        )
        addr, rpc, _ = _resolve_config()
        assert addr == "0xEXPLICIT_ADDR"
        assert rpc == "https://explicit-rpc.com"


class TestResolveConfig:
    """Tests for _resolve_config()."""

    def test_priority_order(self, monkeypatch):
        """rpc_url param > configure() > env var > preset."""
        monkeypatch.setenv("BASE_RPC_URL", "https://env-rpc.com")
        # Contract address required since v0.1.8 — pass through configure
        configure(
            network="sepolia",
            contract_address="0xDEADBEEFc39a17e36ba4a6b4d238ff944bacb478",
            rpc_url="https://configured-rpc.com",
        )

        # Parameter takes highest priority
        _, rpc, _ = _resolve_config(rpc_url="https://param-rpc.com")
        assert rpc == "https://param-rpc.com"

        # Without param, configure() value wins
        _, rpc, _ = _resolve_config()
        assert rpc == "https://configured-rpc.com"

    def test_env_var_fallback(self, monkeypatch):
        """Env var used when no explicit config."""
        monkeypatch.setenv("ANCHOR_REGISTRY_ADDRESS", "0xFROM_ENV")
        monkeypatch.setenv("BASE_RPC_URL", "https://env-rpc.com")
        import anchorregistry.config as cfg

        cfg._active_network = "sepolia"
        cfg._explicit_address = None
        cfg._explicit_rpc_url = None

        addr, rpc, _ = _resolve_config()
        assert addr == "0xFROM_ENV"
        assert rpc == "https://env-rpc.com"

    def test_no_address_raises(self, monkeypatch):
        """ConfigurationError when no address available."""
        import anchorregistry.config as cfg

        cfg._active_network = "base"
        cfg._explicit_address = None
        monkeypatch.delenv("ANCHOR_REGISTRY_ADDRESS", raising=False)

        with pytest.raises(ConfigurationError, match="No contract address"):
            _resolve_config()
