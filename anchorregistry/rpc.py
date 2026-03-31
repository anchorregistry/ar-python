# SPDX-License-Identifier: BUSL-1.1
"""RPC connection and eth_getLogs wrapper.

All on-chain communication is isolated here. Swap this module to change
the RPC transport layer.
"""

from __future__ import annotations

from typing import Any

from web3 import Web3

from anchorregistry.abi import READ_ABI
from anchorregistry.config import _resolve_config

# ── connection cache ──────────────────────────────────────────────────
_w3_cache: dict[str, Web3] = {}


def _connect(rpc_url: str | None = None) -> tuple[Web3, Any, int | None]:
    """Return ``(w3, contract, deploy_block)`` for the resolved config.

    Parameters
    ----------
    rpc_url:
        Explicit RPC URL override. If ``None``, resolved via config.
    """
    addr, resolved_rpc, deploy_block = _resolve_config(rpc_url)

    if resolved_rpc not in _w3_cache:
        _w3_cache[resolved_rpc] = Web3(Web3.HTTPProvider(resolved_rpc))
    w3 = _w3_cache[resolved_rpc]

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(addr), abi=READ_ABI
    )
    return w3, contract, deploy_block


def _get_logs(
    w3: Web3,
    contract_address: str,
    from_block: int,
    to_block: int | str,
    topic_1: str | None = None,
    topic_2: str | None = None,
    topic_3: str | None = None,
) -> list[dict]:
    """Fetch raw Anchored event logs via ``eth_getLogs``.

    Parameters
    ----------
    w3:
        Active Web3 instance.
    contract_address:
        Checksummed contract address.
    from_block:
        Starting block number.
    to_block:
        Ending block number or ``"latest"``.
    topic_1:
        Keccak256 hash of arId (indexed topic 1), or ``None``.
    topic_2:
        Registrant address zero-padded to 32 bytes, or ``None``.
    topic_3:
        Keccak256 hash of treeId (indexed topic 3), or ``None``.

    Returns
    -------
    list[dict]
        Raw log entries from the node.
    """
    event_sig = (
        "0x"
        + Web3.keccak(
            text="Anchored(string,address,uint8,string,string,string,string,string,string,string,string)"
        ).hex()
    )

    topics: list[str | None] = [event_sig, topic_1, topic_2, topic_3]

    # Trim trailing Nones so the RPC doesn't reject extra null topics.
    while topics and topics[-1] is None:
        topics.pop()

    logs = w3.eth.get_logs(
        {
            "address": Web3.to_checksum_address(contract_address),
            "fromBlock": from_block,
            "toBlock": to_block,
            "topics": topics,
        }
    )
    return list(logs)


def _fetch_anchor_data(contract: Any, ar_id: str) -> bytes:
    """Call ``getAnchorData(arId)`` on-chain.

    Returns
    -------
    bytes
        ABI-encoded type-specific extra data.
    """
    return bytes(contract.functions.getAnchorData(ar_id).call())
