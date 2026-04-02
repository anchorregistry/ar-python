# SPDX-License-Identifier: BUSL-1.1
"""Utility functions — DataFrame conversion, topic hashing, helpers."""

from __future__ import annotations

from typing import Any

from web3 import Web3


def _build_topic(value: str) -> str:
    """Compute keccak256 topic hash for an indexed ``string`` parameter.

    Parameters
    ----------
    value:
        Plain string (e.g. AR-ID or treeId) to hash.

    Returns
    -------
    str
        Hex-encoded keccak256 hash prefixed with ``0x``.
    """
    return "0x" + Web3.keccak(text=value).hex()


def _address_topic(address: str) -> str:
    """Convert an Ethereum address to a 32-byte topic hex string.

    Parameters
    ----------
    address:
        Ethereum address (with or without checksum).

    Returns
    -------
    str
        ``0x``-prefixed, zero-padded 32-byte hex string.
    """
    return "0x" + address.lower().replace("0x", "").rjust(64, "0")


def is_user_initiated(record: dict[str, Any]) -> bool:
    """Return True if the anchor was initiated by the token holder.

    An anchor is user-initiated when its ``token_commitment`` is non-zero.
    Governance anchors (VOID, REVIEW, AFFIRMED, RETRACTION) carry
    ``bytes32(0)`` as a sentinel — enforced by the contract.

    Parameters
    ----------
    record:
        Two-level anchor record dict as returned by any query function.

    Returns
    -------
    bool
        ``True`` if user-initiated (non-zero tokenCommitment).
        ``False`` for AR governance actions.

    Examples
    --------
    >>> from anchorregistry import get_by_arid
    >>> from anchorregistry.utils import is_user_initiated
    >>> record = get_by_arid("AR-2026-Pvdp0W5")
    >>> is_user_initiated(record)
    True
    """
    return record["token_commitment"] != "0x" + "0" * 64


def to_dataframe(records: list[dict[str, Any]]) -> Any:
    """Flatten anchor records into a pandas DataFrame.

    Type-specific fields in ``data`` are flattened with
    ``{type_name}_{field_name}`` column names to avoid semantic collision.

    Parameters
    ----------
    records:
        List of two-level anchor record dicts.

    Returns
    -------
    pandas.DataFrame
        Flat DataFrame suitable for analytics.

    Raises
    ------
    ImportError
        If pandas is not installed.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for to_dataframe(). "
            "Install it with: pip install anchorregistry[analytics]"
        ) from None

    rows: list[dict[str, Any]] = []
    for record in records:
        row = {k: v for k, v in record.items() if k != "data"}
        type_name = record.get("artifact_type_name", "unknown").lower()
        for field_name, field_value in record.get("data", {}).items():
            row[f"{type_name}_{field_name}"] = field_value
        rows.append(row)

    return pd.DataFrame(rows)
