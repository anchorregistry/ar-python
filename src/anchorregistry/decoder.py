# SPDX-License-Identifier: BUSL-1.1
"""Decode raw event logs into two-level anchor records.

The critical module — if ``_decode_event`` is correct, everything else follows.
"""

from __future__ import annotations

from typing import Any

from eth_abi import decode
from web3 import Web3

from anchorregistry.types import ARTIFACT_TYPE_MAP, TYPE_ABI, TYPE_FIELDS

# Non-indexed data field types in Anchored event (in order).
_EVENT_DATA_TYPES = [
    "uint8",    # artifactType
    "string",   # arIdPlain
    "string",   # descriptor
    "string",   # title
    "string",   # author
    "string",   # manifestHash
    "string",   # parentArId
    "string",   # treeIdPlain
    "bytes32",  # tokenCommitment — SHA256(ownershipToken + arId), or bytes32(0) for governance
]


def _decode_event(raw_log: dict) -> dict[str, Any]:
    """Decode a single raw Anchored event log into universal fields.

    Parameters
    ----------
    raw_log:
        Raw log dict from ``eth_getLogs`` / web3.

    Returns
    -------
    dict[str, Any]
        Record with universal fields populated.  ``"data"`` key is an
        empty dict — caller fills it via ``_decode_data_fields``.
    """
    # Decode non-indexed data payload.
    values = decode(_EVENT_DATA_TYPES, bytes(raw_log["data"]))
    (
        artifact_type_index,
        ar_id_plain,
        descriptor,
        title,
        author,
        manifest_hash,
        parent_ar_id,
        tree_id_plain,
        token_commitment_bytes,
    ) = values

    # Registrant address from indexed topic 2 (last 20 bytes of 32-byte topic).
    registrant = "0x" + raw_log["topics"][2].hex()[-40:]

    # tokenCommitment: bytes32 → 0x-prefixed hex string.
    # bytes32(0) sentinel = "0x" + "0" * 64 → governance anchor (VOID/REVIEW/AFFIRMED).
    token_commitment = "0x" + token_commitment_bytes.hex()

    return {
        "ar_id": ar_id_plain,
        "registered": True,
        "artifact_type_index": artifact_type_index,
        "artifact_type_name": ARTIFACT_TYPE_MAP.get(artifact_type_index, "UNKNOWN"),
        "tx": "0x" + raw_log["transactionHash"].hex(),
        "block": raw_log["blockNumber"],
        "registrant": registrant,
        "manifest_hash": manifest_hash,
        "parent_ar_id": parent_ar_id,
        "descriptor": descriptor,
        "title": title,
        "author": author,
        "tree_id": tree_id_plain,
        "token_commitment": token_commitment,
        "data": {},
    }


def _decode_data_fields(artifact_type_index: int, raw_extra: bytes) -> dict[str, Any]:
    """Decode ABI-encoded extra bytes into type-specific data dict.

    Parameters
    ----------
    artifact_type_index:
        Integer index of the artifact type (0-22).
    raw_extra:
        ABI-encoded bytes from ``getAnchorData(arId)``.

    Returns
    -------
    dict[str, Any]
        Field names → values for the given artifact type.
    """
    if not raw_extra:
        return {}

    fields = TYPE_FIELDS.get(artifact_type_index)
    abi_types = TYPE_ABI.get(artifact_type_index)
    if fields is None or abi_types is None:
        return {}

    values = decode(list(abi_types), raw_extra)
    return dict(zip(fields, values))
