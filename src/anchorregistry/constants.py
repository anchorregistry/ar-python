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
        "contract_address": "0x9E1F48D3C46bc69a540d16511FaA76Add25A8451",
        "deploy_block": None,  # updated at new tokenCommitment contract deploy
        "chain_id": 11155111,
        "rpc_url": "https://rpc.sepolia.org",
    },
}

# Active-network values — updated by config.configure()
CONTRACT_ADDRESS: str = NETWORKS["base"]["contract_address"]
DEPLOY_BLOCK: int | None = NETWORKS["base"]["deploy_block"]
