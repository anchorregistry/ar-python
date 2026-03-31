# SPDX-License-Identifier: BUSL-1.1
"""Network presets and exported constants for anchorregistry."""

NETWORKS = {
    "base": {
        "contract_address": "TBD",
        "deploy_block": None,
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
    },
    "sepolia": {
        "contract_address": "0x9dAb9f5B754f8C56B5F7BAd3E92A8bDe7317AD29",
        "deploy_block": 10562312,
        "chain_id": 11155111,
        "rpc_url": "https://rpc.sepolia.org",
    },
}

# Active-network values — updated by config.configure()
CONTRACT_ADDRESS: str = NETWORKS["base"]["contract_address"]
DEPLOY_BLOCK: int | None = NETWORKS["base"]["deploy_block"]
