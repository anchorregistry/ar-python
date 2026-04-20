# SPDX-License-Identifier: BUSL-1.1
"""Configuration management for anchorregistry.

Resolution priority (highest first):
1. Explicit rpc_url parameter on the function call
2. configure() call in the current process
3. Environment variables (ANCHOR_REGISTRY_ADDRESS, BASE_RPC_URL, NETWORK)
4. NETWORKS preset for the active network (default: "base")
"""

from __future__ import annotations

import os

import anchorregistry.constants as _constants
from anchorregistry.constants import NETWORKS
from anchorregistry.exceptions import ConfigurationError

# ── module-level state ────────────────────────────────────────────────
_active_network: str = os.environ.get("NETWORK", "base")
_explicit_address:   str | None = None
_explicit_rpc_url:   str | None = None
_explicit_deploy_block: int | None = None


def configure(
    contract_address: str | None = None,
    rpc_url: str | None = None,
    network: str = "base",
    deploy_block: int | None = None,
) -> None:
    """Configure the active network, contract address, RPC, and deploy block.

    Parameters
    ----------
    contract_address:
        AnchorRegistry contract address to read from. Required — either here
        or via the ``ANCHOR_REGISTRY_ADDRESS`` env var. ar-python ships no
        default address so callers are always explicit about which contract
        deployment they're targeting.
    rpc_url:
        Optional RPC URL override. Falls back to ``BASE_RPC_URL`` env var,
        then to the network preset.
    network:
        Network name for chain_id + default rpc_url lookup. One of
        ``"base"``, ``"base-sepolia"``, ``"sepolia"``.
    deploy_block:
        Starting block for ``get_all`` / ``get_by_registrant`` / ``get_by_tree``
        scans. Strongly recommended — omit and scans start at block 0, which
        most RPCs reject on wide ranges.

    Raises
    ------
    ConfigurationError
        If *network* is not a recognised preset name.
    """
    global _active_network, _explicit_address, _explicit_rpc_url, _explicit_deploy_block

    if network not in NETWORKS:
        raise ConfigurationError(
            f"Unknown network: {network!r}. Valid networks: {list(NETWORKS)}"
        )

    _active_network        = network
    _explicit_address      = contract_address
    _explicit_rpc_url      = rpc_url
    _explicit_deploy_block = deploy_block

    # Clear cached Web3 connections so new timeout/RPC settings take effect.
    from anchorregistry.rpc import _w3_cache
    _w3_cache.clear()

    # Keep module-level constants in sync for importers. Swallow the
    # ConfigurationError if no address is set yet — callers may configure()
    # with network only and supply the address later via env var.
    try:
        addr, _, db = _resolve_config()
        _constants.CONTRACT_ADDRESS = addr
        _constants.DEPLOY_BLOCK     = db
    except ConfigurationError:
        pass


def _resolve_config(rpc_url: str | None = None) -> tuple[str, str, int | None]:
    """Resolve (contract_address, rpc_url, deploy_block) from all sources.

    Returns
    -------
    tuple[str, str, int | None]
        ``(contract_address, rpc_url, deploy_block)``

    Raises
    ------
    ConfigurationError
        If no contract address can be resolved.
    """
    preset = NETWORKS.get(_active_network, NETWORKS["base"])

    # Contract address: explicit > env. No preset default — ar-python is
    # agnostic about which deployment you want to read.
    addr = (
        _explicit_address
        or os.environ.get("ANCHOR_REGISTRY_ADDRESS")
    )
    if not addr:
        raise ConfigurationError(
            "No contract address configured. Call "
            "configure(contract_address=...) or set ANCHOR_REGISTRY_ADDRESS."
        )

    # RPC URL: parameter > explicit > env > network preset
    resolved_rpc = (
        rpc_url
        or _explicit_rpc_url
        or os.environ.get("BASE_RPC_URL")
        or preset.get("rpc_url", "")
    )

    # Deploy block: explicit from configure() only. Falls back to None
    # which causes scans to start at block 0 (may be rejected by RPCs that
    # cap block range — callers running get_all should always supply one).
    return addr, resolved_rpc, _explicit_deploy_block
