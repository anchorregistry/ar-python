# SPDX-License-Identifier: BUSL-1.1
"""Network presets and exported constants for anchorregistry.

Presets describe connectivity only (chain_id + rpc_url). Contract address
and deploy block are supplied by the caller via ``configure()`` or the
``ANCHOR_REGISTRY_ADDRESS`` environment variable — ar-python makes no
assumption about which contract deployment you want to read. This keeps
the library decoupled from AnchorRegistry's deployment history.
"""

NETWORKS = {
    "base": {
        "chain_id": 8453,
        "rpc_url":  "https://mainnet.base.org",
    },
    "base-sepolia": {
        "chain_id": 84532,
        "rpc_url":  "https://sepolia.base.org",
    },
    "sepolia": {
        "chain_id": 11155111,
        "rpc_url":  "https://rpc.sepolia.org",
    },
}

# Active-network values — updated by config.configure() when the caller
# supplies a contract_address and/or deploy_block. Left empty until then.
CONTRACT_ADDRESS: str = ""
DEPLOY_BLOCK: int | None = None
