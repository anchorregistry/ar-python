# SPDX-License-Identifier: BUSL-1.1
"""Network presets and exported constants for anchorregistry.

Presets describe connectivity only (chain_id + rpc_url). Contract address
and deploy block are supplied by the caller via ``configure()`` or the
``ANCHOR_REGISTRY_ADDRESS`` environment variable — ar-python makes no
assumption about which contract deployment you want to read. This keeps
the library decoupled from AnchorRegistry's deployment history.
"""

# Default public RPC endpoints per network. Exposed as module-level constants
# so callers can import, inspect, and pass them explicitly into configure():
#
#   from anchorregistry import configure, BASE_SEPOLIA_RPC
#   configure(network="base-sepolia", contract_address="0x…", rpc_url=BASE_SEPOLIA_RPC)
#
# Override by passing your own rpc_url= (Infura / Alchemy / self-hosted) when
# you need higher rate limits or faster single-call scans.
BASE_RPC             = "https://mainnet.base.org"
BASE_SEPOLIA_RPC     = "https://base-sepolia.drpc.org"   # drpc.org accepts 10k-block chunks; sepolia.base.org has a silent-gap bug on historical ranges
ETHEREUM_SEPOLIA_RPC = "https://rpc.sepolia.org"

NETWORKS = {
    "base": {
        "chain_id": 8453,
        "rpc_url":  BASE_RPC,
    },
    "base-sepolia": {
        "chain_id": 84532,
        "rpc_url":  BASE_SEPOLIA_RPC,
    },
    "sepolia": {
        "chain_id": 11155111,
        "rpc_url":  ETHEREUM_SEPOLIA_RPC,
    },
}

# Known AnchorRegistry deployments → their deploy block.
# Looked up by configure() when the caller passes contract_address but omits
# deploy_block, so users don't have to memorize block numbers for the
# contracts ar-python officially supports. Addresses are lowercased for
# case-insensitive lookup. Callers deploying their own fork can still pass
# deploy_block=... explicitly.
KNOWN_DEPLOYMENTS: dict[str, int] = {
    # Base Sepolia — V1 (historical demo anchors live here)
    "0xb0435faa6deedc1cb6a809008516fe4f4b094f76": 40223296,
    # Base Sepolia — V1.1 (Phase 6: AFFIRMED fix + importAnchor)
    "0x1a4a7238d65ce7ed0a2fd65b891290be5af622a8": 40470850,
    # Ethereum Sepolia — original deployment
    "0xe772b7f4ec4a92109b8b892add205ede7c850dba": 10575629,
}

# Active-network values — updated by config.configure() when the caller
# supplies a contract_address / deploy_block / rpc_url. Left empty until
# configure() runs so callers can introspect the live connection settings:
#
#   from anchorregistry.constants import CONTRACT_ADDRESS, DEPLOY_BLOCK, RPC_URL
#   configure(network="base-sepolia", contract_address="0x…", deploy_block=…)
#   print(CONTRACT_ADDRESS, DEPLOY_BLOCK, RPC_URL)
CONTRACT_ADDRESS: str = ""
DEPLOY_BLOCK: int | None = None
RPC_URL: str = ""
