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

# ── constants ────────────────────────────────────────────────────────
# Chunk size for eth_getLogs fallback. 10k clears every public Base-Sepolia
# RPC we've tested (drpc.org, sepolia.base.org at its best, publicnode when up).
# Authenticated RPCs hit the fast path above and skip chunking entirely.
_DEFAULT_CHUNK_SIZE = 10_000

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
        _w3_cache[resolved_rpc] = Web3(
            Web3.HTTPProvider(resolved_rpc, request_kwargs={"timeout": 30})
        )
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
            text="Anchored(string,address,uint8,string,string,string,string,string,string,string,string,bytes32)"
        ).hex()
    )

    topics: list[str | None] = [event_sig, topic_1, topic_2, topic_3]

    # Trim trailing Nones so the RPC doesn't reject extra null topics.
    while topics and topics[-1] is None:
        topics.pop()

    filter_params = {
        "address": Web3.to_checksum_address(contract_address),
        "fromBlock": from_block,
        "toBlock": to_block,
        "topics": topics,
    }

    # Range-aware dispatch: if the whole span fits in one chunk we make a
    # single call (works on every RPC). Otherwise go straight to chunked.
    # Avoids the whack-a-mole of matching provider-specific error strings
    # (Infura says "block range", Alchemy says "exceed", dRPC says "400
    # Bad Request", sepolia.base.org says "413"…) — a wide range is
    # going to fail on at least one of those, so we never bet on it.
    resolved_end = (
        w3.eth.block_number if to_block == "latest" else int(to_block)
    )
    span = resolved_end - from_block + 1

    if span <= _DEFAULT_CHUNK_SIZE:
        return list(w3.eth.get_logs(filter_params))

    all_logs: list[dict] = []
    chunk_start = from_block
    while chunk_start <= resolved_end:
        chunk_end = min(chunk_start + _DEFAULT_CHUNK_SIZE - 1, resolved_end)
        chunk_logs = w3.eth.get_logs(
            {
                "address": filter_params["address"],
                "fromBlock": chunk_start,
                "toBlock": chunk_end,
                "topics": topics,
            }
        )
        all_logs.extend(chunk_logs)
        chunk_start = chunk_end + 1
    return all_logs


def _fetch_anchor_data(contract: Any, ar_id: str) -> bytes:
    """Call ``getAnchorData(arId)`` on-chain.

    Returns
    -------
    bytes
        ABI-encoded type-specific extra data.
    """
    return bytes(contract.functions.getAnchorData(ar_id).call())


def _fetch_anchor_data_batch(
    w3: Web3, contract: Any, ar_ids: list[str]
) -> list[bytes]:
    """Batch-fetch ``getAnchorData`` for multiple AR-IDs in a single RPC call.

    Parameters
    ----------
    w3:
        Active Web3 instance.
    contract:
        Contract instance with ``getAnchorData`` function.
    ar_ids:
        List of AR-ID strings to fetch.

    Returns
    -------
    list[bytes]
        ABI-encoded extra data for each AR-ID, in the same order.
    """
    if not ar_ids:
        return []

    with w3.batch_requests() as batch:
        for ar_id in ar_ids:
            batch.add(contract.functions.getAnchorData(ar_id))
        responses = batch.execute()

    return [bytes(r) for r in responses]


def _fetch_transactions_batch(
    w3: Web3, tx_hashes: list[bytes]
) -> list[dict]:
    """Batch-fetch transactions by hash in a single RPC call.

    Parameters
    ----------
    w3:
        Active Web3 instance.
    tx_hashes:
        List of transaction hashes.

    Returns
    -------
    list[dict]
        Transaction objects in the same order.
    """
    if not tx_hashes:
        return []

    with w3.batch_requests() as batch:
        for tx_hash in tx_hashes:
            batch.add(w3.eth.get_transaction(tx_hash))
        responses = batch.execute()

    return list(responses)
