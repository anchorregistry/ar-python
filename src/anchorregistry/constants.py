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
        "contract_address": "0xE772B7f4eC4a92109b8b892Add205ede7c850DBa",
        "deploy_block": 10575629,  # SEAL contract deploy block (Sepolia)
        "chain_id": 11155111,
        "rpc_url": "https://rpc.sepolia.org",
    },
}

# Active-network values — updated by config.configure()
CONTRACT_ADDRESS: str = NETWORKS["base"]["contract_address"]
DEPLOY_BLOCK: int | None = NETWORKS["base"]["deploy_block"]
