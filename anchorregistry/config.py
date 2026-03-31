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
_explicit_address: str | None = None
_explicit_rpc_url: str | None = None


def configure(
    contract_address: str | None = None,
    rpc_url: str | None = None,
    network: str = "base",
) -> None:
    """Configure the active network, contract address, and RPC endpoint.

    Parameters
    ----------
    contract_address:
        Explicit contract address. Overrides network preset and env var.
    rpc_url:
        Explicit RPC URL. Overrides network preset and env var.
    network:
        Network name — ``"base"`` or ``"sepolia"``. Defaults to ``"base"``.

    Raises
    ------
    ConfigurationError
        If *network* is not a recognised preset name.
    """
    global _active_network, _explicit_address, _explicit_rpc_url

    if network not in NETWORKS:
        raise ConfigurationError(
            f"Unknown network: {network!r}. Valid networks: {list(NETWORKS)}"
        )

    _active_network = network
    _explicit_address = contract_address
    _explicit_rpc_url = rpc_url

    # Keep module-level constants in sync for importers.
    addr, _, deploy_block = _resolve_config()
    _constants.CONTRACT_ADDRESS = addr
    _constants.DEPLOY_BLOCK = deploy_block


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

    # Contract address: explicit > env > preset
    addr = (
        _explicit_address
        or os.environ.get("ANCHOR_REGISTRY_ADDRESS")
        or preset["contract_address"]
    )
    if not addr or addr == "TBD":
        raise ConfigurationError(
            "No contract address configured. "
            "Call configure() or set ANCHOR_REGISTRY_ADDRESS."
        )

    # RPC URL: parameter > explicit > env > preset
    resolved_rpc = (
        rpc_url
        or _explicit_rpc_url
        or os.environ.get("BASE_RPC_URL")
        or preset["rpc_url"]
    )

    # Deploy block: preset (updated by configure via network selection)
    deploy_block = preset["deploy_block"]

    return addr, resolved_rpc, deploy_block
