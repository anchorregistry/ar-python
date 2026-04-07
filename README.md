# anchorregistry

**Trustless Python client for the AnchorRegistry provenance chain on Base (Ethereum L2).**

`anchorregistry` reads provenance records directly from the Base blockchain — no intermediary API, no account, no API key. It is the same library used in AnchorRegistry's own production backend.

Verify what existed, when, and who registered it — directly from the chain.

**DAPX-Anchor: [anchorregistry.ai/AR-2026-0000001](https://anchorregistry.ai/AR-2026-0000001)**

---

## Installation

```bash
pip install anchorregistry

# With DataFrame support
pip install anchorregistry[analytics]
```

Requires Python 3.11+

---

## Quickstart

```python
from anchorregistry import get_by_arid

record = get_by_arid("AR-2026-Pvdp0W5")
print(record["title"])        # DeFiPy GitHub
print(record["author"])       # Ian Moore
print(record["manifest_hash"])
print(record["data"]["language"])  # Python
```

---

## Usage

### Query by AR-ID
```python
from anchorregistry import get_by_arid

record = get_by_arid("AR-2026-Pvdp0W5")
```

### Query by registrant wallet
```python
from anchorregistry import get_by_registrant

records = get_by_registrant("0xc7a7afde1177fbf0bb265ea5a616d1b8d7ed8c44")
```

### Query by tree
```python
from anchorregistry import get_by_tree

records = get_by_tree("ar-operator-v1")
```

### Query by artifact type
```python
from anchorregistry import get_by_type
from anchorregistry.enums import ArtifactType

records = get_by_type(ArtifactType.CODE)
```

### Full registry harvest
```python
from anchorregistry import get_all

records = get_all()                                          # full registry
records = get_all(from_block=10000000)                       # from block
records = get_all(from_block=10000000, to_block=10500000)    # block range
```

### Verify file integrity
```python
from anchorregistry import verify

result = verify("AR-2026-Pvdp0W5")                          # record only
result = verify("AR-2026-Pvdp0W5", file_path="./myfile.py") # + SHA256 check
print(result["hash_match"])  # True / False
```

### Generate watermark tag
```python
from anchorregistry import watermark

line = watermark("AR-2026-Pvdp0W5", artifact_type="CODE")
# → "SPDX-Anchor: anchorregistry.ai/AR-2026-Pvdp0W5"

line = watermark("AR-2026-Pvdp0W5", artifact_type="RESEARCH")
# → "DAPX-Anchor: anchorregistry.ai/AR-2026-Pvdp0W5"

# Resolves type from chain if not provided
line = watermark("AR-2026-Pvdp0W5")
```

### Authenticate anchor ownership
```python
from anchorregistry import authenticate_anchor

result = authenticate_anchor("0xabc123...", "AR-2026-Pvdp0W5")
print(result["authenticated"])  # True / False
```

The ownership token (`K`) is a `0x`-prefixed bytes32 hex string generated client-side at registration time via `keccak256(salt)`. It is never transmitted on-chain — only the commitment `keccak256(K || arId)` is stored.

### Authenticate a full tree
```python
from anchorregistry import authenticate_tree

result = authenticate_tree("0xabc123...", "AR-2026-Pvdp0W5")
print(result["authenticated"])      # True if tree ownership + all anchors verified
print(result["anchors_verified"])   # count of verified user-initiated anchors
print(result["governance_count"])   # governance anchors (skipped, bytes32(0))
```

Two-layer verification: Layer 1 checks tree ownership via `keccak256(K || rootArId) == treeId`, Layer 2 verifies every user-initiated anchor's `tokenCommitment` in the tree.

### Analytics — load into DataFrame
```python
from anchorregistry import get_all, to_dataframe

df = to_dataframe(get_all())
df[df.artifact_type_name == "CODE"]
df[df.author == "Ian Moore"]
df.groupby("artifact_type_name").count()
```

---

## Network Configuration

Works identically against Base mainnet and Sepolia testnet.

```python
from anchorregistry import configure

# Mainnet (default)
configure(network="base")

# Sepolia testnet
configure(network="sepolia")

# Custom RPC
configure(network="base", rpc_url="https://my-rpc-node.com")
```

Or via environment variables:
```bash
export NETWORK=sepolia
export BASE_RPC_URL=https://my-rpc-node.com
export ANCHOR_REGISTRY_ADDRESS=0x...
```

---

## Record Structure

Every record follows a consistent two-level structure regardless of artifact type:

```python
{
    # Universal fields — identical for every type
    "ar_id":                "AR-2026-Pvdp0W5",
    "registered":           True,
    "artifact_type_index":  0,
    "artifact_type_name":   "CODE",
    "tx":                   "0xe36116...",
    "block":                10533679,
    "registrant":           "0xc7a7af...",
    "manifest_hash":        "3e2d69...",
    "parent_ar_id":         "",
    "descriptor":           "DeFiPy: Python SDK for DeFi Analytics and Agents",
    "title":                "DeFiPy GitHub",
    "author":               "Ian Moore",
    "tree_id":              "ar-operator-v1",
    "token_commitment":     "0x3e2d69...",   # keccak256(K || arId), bytes32(0) for governance

    # Type-specific fields — only fields for this artifact type
    "data": {
        "git_hash":  "18afe3d...",
        "license":   "MIT",
        "language":  "Python",
        "version":   "v1.0.0",
        "url":       "https://github.com/defipy-devs/defipy"
    }
}
```

---

## Watermark Standards

AnchorRegistry defines two watermark standards for embedding a provenance signal in any artifact:

**SPDX-Anchor** — for software (code, packages, repositories)
```
SPDX-Anchor: anchorregistry.ai/AR-2026-XXXXXXX
```

**DAPX-Anchor** — for all other artifacts (research, data, models, media, legal, proofs)
```
DAPX-Anchor: anchorregistry.ai/AR-2026-XXXXXXX
```

One line signals membership in a provenance tree — queryable by humans and AI agents alike.

---

## Exported Constants

```python
from anchorregistry import ARTIFACT_TYPE_MAP, READ_ABI, CONTRACT_ADDRESS, DEPLOY_BLOCK
```

`ARTIFACT_TYPE_MAP` and `READ_ABI` are the canonical source of truth for AnchorRegistry type ordering and ABI — used by AnchorRegistry's production backend directly.

---

## Design

- **Trustless.** Reads directly from Base blockchain events via RPC. No AnchorRegistry servers involved.
- **Read-only.** Registration happens through anchorregistry.com. This package only reads.
- **No auth required.** Verification is open and free to anyone with an RPC endpoint.
- **Production parity.** The same library powering the AnchorRegistry backend — not a wrapper.
- **Network-agnostic.** Works identically against Base mainnet and Sepolia testnet.
- **Built on Base.** Base settles to Ethereum mainnet — provenance anchors inherit Ethereum-grade finality.

---

## Testing

### Unit tests (no RPC required)

```bash
python3 -m pytest tests/ -v --ignore=tests/test_client.py
```

### Full suite with Sepolia integration tests

Create a `.env` file with your Sepolia RPC endpoint:

```bash
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
```

For authentication integration tests, also set:

```bash
ANCHOR_OWNERSHIP_TOKEN=0x...   # 0x-prefixed bytes32 hex (keccak256 token)
ANCHOR_ROOT_AR_ID=AR-2026-...  # root AR-ID for the ownership token
```

Then run:

```bash
set -a && source .env && set +a && python3 -m pytest tests/ -v
```

Integration tests in `test_client.py` are automatically skipped when `SEPOLIA_RPC_URL` is not set. Authentication tests are additionally skipped when `ANCHOR_OWNERSHIP_TOKEN` and `ANCHOR_ROOT_AR_ID` are not set.

---

## References

The cryptographic commitment scheme and security proofs underlying this implementation
are formally described in:

**Trustless Provenance Trees: A Game-Theoretic Framework for Operator-Gated Blockchain Registries**
Ian C. Moore — *arXiv:2604.03434 [cs.GT], April 2026*
https://arxiv.org/abs/2604.03434

## Status

> Alpha. Core library under active development against Sepolia testnet. API surface stable per spec. Not yet published to PyPI.

---

## License

Business Source License 1.1 (BUSL-1.1)  
Change Date: March 12, 2028 → Apache License 2.0  
Licensor: Ian Moore

---

## Links

- Website: [anchorregistry.com](https://anchorregistry.com)
- Verify: [anchorregistry.ai](https://anchorregistry.ai)
- Docs: [anchorregistry.readthedocs.io](https://anchorregistry.readthedocs.io)
- PyPI: [pypi.org/project/anchorregistry](https://pypi.org/project/anchorregistry)
- Source: [github.com/anchorregistry/ar-python](https://github.com/anchorregistry/ar-python)
