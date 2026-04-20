# SPDX-License-Identifier: BUSL-1.1
# DAPX-Anchor: anchorregistry.ai/TBD
"""
anchorregistry — Trustless Python client for the AnchorRegistry smart contract.

Reads provenance data directly from on-chain events via RPC with zero
dependency on AnchorRegistry infrastructure.
"""

__version__ = "0.1.8"

from anchorregistry.client import (
    get_by_arid,
    get_by_registrant,
    get_by_tree,
    get_by_type,
    get_all,
    verify,
    watermark,
    authenticate_anchor,
    authenticate_tree,
    is_sealed,
)
from anchorregistry.config import configure
from anchorregistry.utils import to_dataframe, is_user_initiated
from anchorregistry.types import ARTIFACT_TYPE_MAP
from anchorregistry.abi import READ_ABI
from anchorregistry.constants import (
    CONTRACT_ADDRESS,
    DEPLOY_BLOCK,
    RPC_URL,
    BASE_RPC,
    BASE_SEPOLIA_RPC,
    ETHEREUM_SEPOLIA_RPC,
    V1_BASE_SEPOLIA,
    V1_1_BASE_SEPOLIA,
    V1_ETH_SEPOLIA,
    KNOWN_DEPLOYMENTS,
)
from anchorregistry.exceptions import AnchorNotFoundError, ConfigurationError

__all__ = [
    "get_by_arid",
    "get_by_registrant",
    "get_by_tree",
    "get_by_type",
    "get_all",
    "verify",
    "watermark",
    "authenticate_anchor",
    "authenticate_tree",
    "is_sealed",
    "configure",
    "to_dataframe",
    "is_user_initiated",
    "ARTIFACT_TYPE_MAP",
    "READ_ABI",
    "CONTRACT_ADDRESS",
    "DEPLOY_BLOCK",
    "RPC_URL",
    "BASE_RPC",
    "BASE_SEPOLIA_RPC",
    "ETHEREUM_SEPOLIA_RPC",
    "V1_BASE_SEPOLIA",
    "V1_1_BASE_SEPOLIA",
    "V1_ETH_SEPOLIA",
    "KNOWN_DEPLOYMENTS",
    "AnchorNotFoundError",
    "ConfigurationError",
]
