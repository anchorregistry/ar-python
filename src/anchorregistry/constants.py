# SPDX-License-Identifier: BUSL-1.1
"""Network presets and exported constants for anchorregistry.

V0.2.0 — each network preset declares a `deployments` list (newest first).
Multi-deployment scanners in client.py iterate every entry so AR-IDs on any
prior contract remain discoverable. Single-call callers (configure() with an
explicit contract_address) get the legacy single-contract behaviour.
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

# Named AnchorRegistry deployment addresses. Importable so call sites read as
# `contract_address=V1A_BASE_SEPOLIA` instead of bare hex strings.
# Naming convention: V<major><iteration_letter>_<NETWORK> — V1A is the first
# V1-series deployment, V1B the next iteration within V1, etc. When the
# major version changes, restart at V2A, V2B, …
V1A_BASE_SEPOLIA = "0xb0435faa6deedc1cb6a809008516fe4f4b094f76"
V1B_BASE_SEPOLIA = "0xd2cd0064cfb843cf62d3f7e63c195809af0152b7"   # V1.1-final (simplified — log writer only)
V1A_ETH_SEPOLIA  = "0xe772b7f4ec4a92109b8b892add205ede7c850dba"

NETWORKS = {
    "base": {
        "chain_id":    8453,
        "rpc_url":     BASE_RPC,
        "deployments": [],   # populated after Base mainnet deploy
    },
    "base-sepolia": {
        "chain_id": 84532,
        "rpc_url":  BASE_SEPOLIA_RPC,
        # Newest first — multi-deployment scanners walk in this order.
        "deployments": [
            {
                "contract_address": V1B_BASE_SEPOLIA,
                "deploy_block":     40480193,
                "label":            "V1B",
            },
            {
                "contract_address": V1A_BASE_SEPOLIA,
                "deploy_block":     40223296,
                "label":            "V1A",
            },
        ],
    },
    "sepolia": {
        "chain_id": 11155111,
        "rpc_url":  ETHEREUM_SEPOLIA_RPC,
        "deployments": [
            {
                "contract_address": V1A_ETH_SEPOLIA,
                "deploy_block":     10575629,
                "label":            "V1A",
            },
        ],
    },
}

# Derived from NETWORKS — single source of truth above. configure() looks
# these up when the caller passes contract_address but omits deploy_block,
# and which_contract() filters candidates by network membership.
KNOWN_DEPLOYMENTS: dict[str, int] = {
    dep["contract_address"]: dep["deploy_block"]
    for net in NETWORKS.values()
    for dep in net.get("deployments", [])
}
DEPLOYMENT_NETWORKS: dict[str, str] = {
    dep["contract_address"]: net_name
    for net_name, net in NETWORKS.items()
    for dep in net.get("deployments", [])
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
