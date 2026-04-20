# SPDX-License-Identifier: BUSL-1.1
"""Public query functions for anchorregistry.

All functions compose on ``rpc._get_logs`` + ``decoder._decode_event``.
"""

from __future__ import annotations

import hashlib
from typing import Any

from eth_hash.auto import keccak

from eth_abi import decode as abi_decode

from anchorregistry.decoder import _decode_data_fields, _decode_event
from anchorregistry.enums import ArtifactType
from anchorregistry.exceptions import AnchorNotFoundError
from anchorregistry.rpc import (
    _connect,
    _fetch_anchor_data,
    _fetch_anchor_data_batch,
    _fetch_transactions_batch,
    _get_logs,
)
from anchorregistry.utils import _address_topic, _build_topic, is_user_initiated

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

def _decode_target_ar_id(tx: dict) -> str:
    """Decode ``targetArId`` from a ``registerTargeted`` transaction object."""
    calldata = bytes(tx["input"])[4:]  # strip 4-byte function selector
    _, _, target_ar_id, _ = abi_decode(_TARGETED_INPUT_TYPES, calldata)
    return target_ar_id


def _fetch_target_ar_id(w3: Any, tx_hash: bytes) -> str:
    """Decode ``targetArId`` from a ``registerTargeted`` transaction.

    Fetches the transaction by hash and ABI-decodes the calldata to
    extract the ``targetArId`` parameter.
    """
    tx = w3.eth.get_transaction(tx_hash)
    return _decode_target_ar_id(tx)


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


def _build_records(w3: Any, contract: Any, logs: list[dict]) -> list[dict[str, Any]]:
    """Build complete two-level records from multiple logs using batch RPC.

    Sends all ``getAnchorData`` calls in a single batch request, and
    all ``eth_getTransaction`` calls for targeted types in a second batch.
    Reduces N+1 RPC calls to 1 ``eth_getLogs`` + 1 batch ``getAnchorData``
    + 1 batch ``eth_getTransaction``.
    """
    if not logs:
        return []

    # Phase 1: decode all events (no RPC needed).
    records = [_decode_event(log) for log in logs]
    ar_ids = [r["ar_id"] for r in records]

    # Phase 2: batch-fetch all type-specific data.
    extras = _fetch_anchor_data_batch(w3, contract, ar_ids)

    # Phase 3: batch-fetch transactions for targeted types.
    targeted_indices = [
        i for i, r in enumerate(records) if r["artifact_type_index"] in _TARGETED_TYPES
    ]
    targeted_tx_hashes = [logs[i]["transactionHash"] for i in targeted_indices]
    targeted_txs = _fetch_transactions_batch(w3, targeted_tx_hashes)

    # Phase 4: assemble records.
    targeted_tx_map = dict(zip(targeted_indices, targeted_txs))

    for i, record in enumerate(records):
        type_idx = record["artifact_type_index"]
        data = _decode_data_fields(type_idx, extras[i])

        if i in targeted_tx_map:
            data["target_ar_id"] = _decode_target_ar_id(targeted_tx_map[i])

        record["data"] = data

    return records


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
    # AR-IDs are unique → only one matching log can exist. Tell _get_logs to
    # stop scanning subsequent chunks once it finds the hit. Big win on
    # public RPCs that cap eth_getLogs ranges (drpc.org → 26 chunks → 1).
    logs = _get_logs(
        w3, contract.address, deploy_block or 0, "latest",
        topic_1=topic, early_exit_on_match=True,
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
    return _build_records(w3, contract, logs)


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
    return _build_records(w3, contract, logs)


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
    return _build_records(w3, contract, logs)


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


def authenticate_anchor(
    ownership_token: str,
    ar_id: str,
    rpc_url: str | None = None,
) -> dict[str, Any]:
    """Authenticate a single anchor by verifying its tokenCommitment on-chain.

    Computes ``keccak256(K || arId)`` (paper spec Section 4.2) and compares
    the result against the ``token_commitment`` stored in the on-chain
    ``Anchored`` event. Governance anchors (VOID, REVIEW, AFFIRMED, RETRACTION)
    carry ``bytes32(0)`` and are returned as ``authenticated: False`` immediately.

    Parameters
    ----------
    ownership_token:
        Ownership token K = keccak256(salt), salt = 32 uniform random bytes.
        Stored as 0x-prefixed 64-char hex string (bytes32).
        Never transmitted to AnchorRegistry — known only to the token holder.
    ar_id:
        The AR-ID to authenticate (e.g. ``"AR-2026-Pvdp0W5"``).
    rpc_url:
        Optional RPC URL override.

    Returns
    -------
    dict[str, Any]
        Result dict with keys:

        - ``authenticated`` — bool: True if keccak256 proof matches on-chain commitment.
        - ``ar_id`` — str: the AR-ID that was checked.
        - ``token_commitment`` — str: on-chain commitment (``0x``-prefixed bytes32 hex).
        - ``is_user_initiated`` — bool: False for governance anchors (bytes32(0)).
        - ``verified`` — bool: same as ``authenticated``.

    Raises
    ------
    AnchorNotFoundError
        If the AR-ID does not exist on-chain.

    Examples
    --------
    >>> from anchorregistry import configure, authenticate_anchor
    >>> configure(network="sepolia")
    >>> result = authenticate_anchor("0x1a2b3c4d...", "AR-2026-Pvdp0W5")
    >>> result["authenticated"]
    True
    """
    record = get_by_arid(ar_id, rpc_url=rpc_url)
    user_initiated = is_user_initiated(record)

    if not user_initiated:
        return {
            "authenticated": False,
            "ar_id": ar_id,
            "token_commitment": record["token_commitment"],
            "is_user_initiated": False,
            "verified": False,
        }

    # Paper spec Section 4.2: Φi = H(K || Ci), H = keccak256
    # K: bytes32 from 0x-prefixed hex string; Ci: AR-ID as UTF-8 bytes
    K_bytes = bytes.fromhex(ownership_token[2:])
    Ci_bytes = ar_id.encode("utf-8")
    computed = "0x" + keccak(K_bytes + Ci_bytes).hex()
    on_chain = record["token_commitment"]
    verified = computed == on_chain

    return {
        "authenticated": verified,
        "ar_id": ar_id,
        "token_commitment": on_chain,
        "is_user_initiated": True,
        "verified": verified,
    }


def is_sealed(
    root_ar_id: str,
    rpc_url: str | None = None,
) -> dict[str, Any]:
    """Check if a tree root has been sealed on-chain.

    Parameters
    ----------
    root_ar_id:
        AR-ID of the tree root anchor.
    rpc_url:
        Optional RPC URL override.

    Returns
    -------
    dict[str, Any]
        Result dict with keys:

        - ``sealed`` — bool: True if the tree root is sealed.
        - ``continuation`` — str: new tree root if set, empty string otherwise.
    """
    w3, contract, _ = _connect(rpc_url=rpc_url)
    sealed = contract.functions.isSealed(root_ar_id).call()
    continuation = ""
    if sealed:
        continuation = contract.functions.sealContinuation(root_ar_id).call()
    return {
        "sealed": sealed,
        "continuation": continuation,
    }


def authenticate_tree(
    ownership_token: str,
    root_ar_id: str,
    rpc_url: str | None = None,
) -> dict[str, Any]:
    """Authenticate a full tree by verifying ownership and all anchor commitments.

    If the tree is sealed, returns immediately with sealed status — the tree
    is authentic and complete, no further verification needed.

    Two-layer verification:

    **Layer 1 — Tree ownership:**
    Computes ``keccak256(K || rootArId)`` (paper spec Section 4.2) and compares
    against ``record["tree_id"]``. Returns ``authenticated: False`` immediately
    on failure.

    **Layer 2 — Per-anchor initiation:**
    Calls ``get_by_tree()`` and runs ``authenticate_anchor()`` for each
    user-initiated anchor. Governance anchors (bytes32(0) commitment) are
    counted separately and skipped from verification.

    Parameters
    ----------
    ownership_token:
        Ownership token K = keccak256(salt), salt = 32 uniform random bytes.
        Stored as 0x-prefixed 64-char hex string (bytes32).
    root_ar_id:
        AR-ID of the tree root anchor.
    rpc_url:
        Optional RPC URL override.

    Returns
    -------
    dict[str, Any]
        Result dict with keys:

        - ``authenticated`` — bool: True if Layer 1 passes and ``anchors_failed == 0``.
        - ``sealed`` — bool: True if the tree is sealed.
        - ``continuation`` — str: new tree root (if sealed with continuation).
        - ``tree_id`` — str: human-readable treeId from the root anchor.
        - ``root_ar_id`` — str: the root AR-ID that was checked.
        - ``anchor_count`` — int: total anchors in the tree.
        - ``anchors_verified`` — int: user-initiated anchors whose commitment matched.
        - ``anchors_failed`` — int: user-initiated anchors whose commitment did not match.
        - ``governance_count`` — int: governance anchors skipped (bytes32(0)).

    Raises
    ------
    AnchorNotFoundError
        If ``root_ar_id`` does not exist on-chain.

    Examples
    --------
    >>> from anchorregistry import configure, authenticate_tree
    >>> configure(network="sepolia")
    >>> result = authenticate_tree("0x1a2b3c4d...", "AR-2026-Pvdp0W5")
    >>> result["authenticated"]
    True
    """
    # Check sealed status first — sealed trees are authentic and complete.
    seal_status = is_sealed(root_ar_id, rpc_url=rpc_url)
    if seal_status["sealed"]:
        root_record = get_by_arid(root_ar_id, rpc_url=rpc_url)
        return {
            "authenticated": False,
            "sealed": True,
            "continuation": seal_status["continuation"],
            "tree_id": root_record["tree_id"],
            "root_ar_id": root_ar_id,
            "anchor_count": 0,
            "anchors_verified": 0,
            "anchors_failed": 0,
            "governance_count": 0,
            "message": (
                "Tree sealed — record authentic and complete. "
                f"Continued at {seal_status['continuation']}"
                if seal_status["continuation"]
                else "Tree sealed — record authentic and complete."
            ),
        }

    root_record = get_by_arid(root_ar_id, rpc_url=rpc_url)
    tree_id = root_record["tree_id"]

    # Layer 1: verify tree ownership — keccak256(K || R) == treeId
    # Paper spec Section 4.2: T = H(K || R), H = keccak256
    K_bytes = bytes.fromhex(ownership_token[2:])
    R_bytes = root_ar_id.encode("utf-8")
    computed_tree_id = "0x" + keccak(K_bytes + R_bytes).hex()
    layer1_pass = computed_tree_id == tree_id

    if not layer1_pass:
        return {
            "authenticated": False,
            "sealed": False,
            "continuation": "",
            "tree_id": tree_id,
            "root_ar_id": root_ar_id,
            "anchor_count": 0,
            "anchors_verified": 0,
            "anchors_failed": 0,
            "governance_count": 0,
        }

    # Layer 2: verify every user-initiated anchor in the tree.
    tree_records = get_by_tree(tree_id, rpc_url=rpc_url)
    anchors_verified = 0
    anchors_failed = 0
    governance_count = 0

    for anchor in tree_records:
        if not is_user_initiated(anchor):
            governance_count += 1
            continue
        result = authenticate_anchor(ownership_token, anchor["ar_id"], rpc_url=rpc_url)
        if result["verified"]:
            anchors_verified += 1
        else:
            anchors_failed += 1

    return {
        "authenticated": anchors_failed == 0,
        "sealed": False,
        "continuation": "",
        "tree_id": tree_id,
        "root_ar_id": root_ar_id,
        "anchor_count": len(tree_records),
        "anchors_verified": anchors_verified,
        "anchors_failed": anchors_failed,
        "governance_count": governance_count,
    }
