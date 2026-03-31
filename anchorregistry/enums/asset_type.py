# SPDX-License-Identifier: BUSL-1.1
"""OnChain asset types for the ONCHAIN artifact type."""

from enum import StrEnum


class AssetType(StrEnum):
    """Asset types for on-chain artifacts."""

    ADDRESS = "ADDRESS"
    TRANSACTION = "TRANSACTION"
    CONTRACT = "CONTRACT"
    NFT = "NFT"
    TOKEN = "TOKEN"
    DAO = "DAO"
    MULTISIG = "MULTISIG"
