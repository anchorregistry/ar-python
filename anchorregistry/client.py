# SPDX-License-Identifier: BUSL-1.1
"""Public query functions for anchorregistry.

All functions compose on ``rpc._get_logs`` + ``decoder._decode_event``.
"""

from __future__ import annotations

import hashlib
from typing import Any

from eth_abi import decode as abi_decode

from anchorregistry.decoder import _decode_data_fields, _decode_event
from anchorregistry.enums import ArtifactType
from anchorregistry.exceptions import AnchorNotFoundError
from anchorregistry.rpc import _connect, _fetch_anchor_data, _get_logs
from anchorregistry.utils import _address_topic, _build_topic

# Artifact types registered via registerTargeted (have a targetArId param).
_TARGETED_TYPES = {
    ArtifactType.RETRACTION,
    ArtifactType.REVIEW,
    ArtifactType.VOID,
    ArtifactType.AFFIRMED,
}

# ABI types for decoding registerTargeted calldata (after 4-byte selector).
_TARGETED_INPUT_TYPES = [
    "string",                                                    # arId
    "(uint8,string,string,string,string,string,string)",         # AnchorBase tuple
    "string",                                                    # targetArId
    "bytes",                                                     # extra
]

SOFTWARE_TYPES = {"CODE"}


# ── internal helpers ──────────────────────────────────────────────────

def _fetch_target_ar_id(w3: Any, tx_hash: bytes) -> str:
    """Decode ``targetArId`` from a ``registerTargeted`` transaction.

    Fetches the transaction by hash and ABI-decodes the calldata to
    extract the ``targetArId`` parameter.
    """
    tx = w3.eth.get_transaction(tx_hash)
    calldata = bytes(tx["input"])[4:]  # strip 4-byte function selector
    _, _, target_ar_id, _ = abi_decode(_TARGETED_INPUT_TYPES, calldata)
    return target_ar_id


def _build_record(w3: Any, contract: Any, raw_log: dict) -> dict[str, Any]:
    """Build a complete two-level record from a raw Anchored event log."""
    record = _decode_event(raw_log)
    ar_id = record["ar_id"]
    type_idx = record["artifact_type_index"]

    # Fetch and decode type-specific data from on-chain storage.
    extra = _fetch_anchor_data(contract, ar_id)
    data = _decode_data_fields(type_idx, extra)

    # For targeted types, recover targetArId from transaction calldata.
    if type_idx in _TARGETED_TYPES:
        target_ar_id = _fetch_target_ar_id(w3, raw_log["transactionHash"])
        data["target_ar_id"] = target_ar_id

    record["data"] = data
    return record


# ── public API ────────────────────────────────────────────────────────

def get_by_arid(ar_id: str, rpc_url: str | None = None) -> dict[str, Any]:
    """Fetch a single anchor record by AR-ID.

    Uses the indexed ``arId`` topic for a targeted single-event query.

    Parameters
    ----------
    ar_id:
        The AR-ID to look up (e.g. ``"AR-2026-Pvdp0W5"``).
    rpc_url:
        Optional RPC URL override.

    Returns
    -------
    dict[str, Any]
        Two-level anchor record.

    Raises
    ------
    AnchorNotFoundError
        If the AR-ID does not exist on-chain.
    """
    w3, contract, deploy_block = _connect(rpc_url)
    topic = _build_topic(ar_id)
    logs = _get_logs(
        w3, contract.address, deploy_block or 0, "latest", topic_1=topic
    )
    if not logs:
        raise AnchorNotFoundError(f"AR-ID not found on-chain: {ar_id}")
    return _build_record(w3, contract, logs[0])


def get_by_registrant(
    wallet_address: str, rpc_url: str | None = None
) -> list[dict[str, Any]]:
    """Fetch all anchors registered by a specific wallet address.

    Uses the indexed ``registrant`` topic.

    Parameters
    ----------
    wallet_address:
        Ethereum wallet address (checksummed or lowercase).
    rpc_url:
        Optional RPC URL override.

    Returns
    -------
    list[dict[str, Any]]
        List of two-level anchor records.
    """
    w3, contract, deploy_block = _connect(rpc_url)
    topic = _address_topic(wallet_address)
    logs = _get_logs(
        w3, contract.address, deploy_block or 0, "latest", topic_2=topic
    )
    return [_build_record(w3, contract, log) for log in logs]


def get_by_tree(
    tree_id_plain: str, rpc_url: str | None = None
) -> list[dict[str, Any]]:
    """Fetch all anchors belonging to a specific tree.

    Uses the indexed ``treeId`` topic.

    Parameters
    ----------
    tree_id_plain:
        Human-readable treeId string (e.g. ``"ar-operator-v1"``).
    rpc_url:
        Optional RPC URL override.

    Returns
    -------
    list[dict[str, Any]]
        List of two-level anchor records.
    """
    w3, contract, deploy_block = _connect(rpc_url)
    topic = _build_topic(tree_id_plain)
    logs = _get_logs(
        w3, contract.address, deploy_block or 0, "latest", topic_3=topic
    )
    return [_build_record(w3, contract, log) for log in logs]


def get_by_type(
    artifact_type: ArtifactType | int, rpc_url: str | None = None
) -> list[dict[str, Any]]:
    """Fetch all anchors of a specific artifact type.

    Post-filter on decoded ``artifactType`` from event data.

    Parameters
    ----------
    artifact_type:
        An ``ArtifactType`` enum member or its integer index.
    rpc_url:
        Optional RPC URL override.

    Returns
    -------
    list[dict[str, Any]]
        List of two-level anchor records matching the type.
    """
    type_index = int(artifact_type)
    records = get_all(rpc_url=rpc_url)
    return [r for r in records if r["artifact_type_index"] == type_index]


def get_all(
    from_block: int | None = None,
    to_block: int | None = None,
    rpc_url: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch all anchors from the registry.

    Defaults to scanning from ``DEPLOY_BLOCK`` to latest.

    Parameters
    ----------
    from_block:
        Starting block number. Defaults to ``DEPLOY_BLOCK``.
    to_block:
        Ending block number. Defaults to ``"latest"``.
    rpc_url:
        Optional RPC URL override.

    Returns
    -------
    list[dict[str, Any]]
        List of all two-level anchor records.
    """
    w3, contract, deploy_block = _connect(rpc_url)
    start = from_block if from_block is not None else (deploy_block or 0)
    end = to_block if to_block is not None else "latest"
    logs = _get_logs(w3, contract.address, start, end)
    return [_build_record(w3, contract, log) for log in logs]


def verify(
    ar_id: str,
    file_path: str | None = None,
    rpc_url: str | None = None,
) -> dict[str, Any]:
    """Fetch anchor record and optionally verify file integrity.

    If *file_path* is provided, computes SHA256 of the file and compares
    against ``manifest_hash`` on-chain.

    Parameters
    ----------
    ar_id:
        The AR-ID to verify.
    file_path:
        Optional local file path for SHA256 integrity check.
    rpc_url:
        Optional RPC URL override.

    Returns
    -------
    dict[str, Any]
        Record dict plus ``verified`` (bool) and ``hash_match`` (bool) keys.

    Raises
    ------
    AnchorNotFoundError
        If the AR-ID does not exist on-chain.
    """
    record = get_by_arid(ar_id, rpc_url=rpc_url)
    result = {**record, "verified": True, "hash_match": None}

    if file_path is not None:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        file_hash = sha256.hexdigest()
        result["hash_match"] = file_hash == record["manifest_hash"]

    return result


def watermark(
    ar_id: str,
    artifact_type: str | None = None,
    rpc_url: str | None = None,
) -> str:
    """Generate the correct SPDX-Anchor or DAPX-Anchor embedded tag.

    - ``artifact_type == "CODE"`` → ``SPDX-Anchor: anchorregistry.ai/{ar_id}``
    - All other types → ``DAPX-Anchor: anchorregistry.ai/{ar_id}``
    - If *artifact_type* is ``None``, resolves via ``get_by_arid()`` automatically.

    Parameters
    ----------
    ar_id:
        The AR-ID to watermark.
    artifact_type:
        Optional type name string (e.g. ``"CODE"``). If ``None``, looked up
        on-chain.
    rpc_url:
        Optional RPC URL override.

    Returns
    -------
    str
        The watermark line, e.g. ``"SPDX-Anchor: anchorregistry.ai/AR-2026-Pvdp0W5"``.
    """
    if artifact_type is None:
        record = get_by_arid(ar_id, rpc_url=rpc_url)
        artifact_type = record["artifact_type_name"]

    prefix = "SPDX-Anchor" if artifact_type in SOFTWARE_TYPES else "DAPX-Anchor"
    return f"{prefix}: anchorregistry.ai/{ar_id}"
