# anchorregistry — Python Package Specification

**Author:** Ian Moore (icmoore)  
**Date:** March 31, 2026  
**Status:** Pre-build spec — validated against Sepolia testnet before mainnet launch  
**PyPI name:** `anchorregistry`  
**License:** BUSL-1.1 (Change Date: March 12, 2028 → Apache-2.0)

---

## 1. Purpose & Positioning

`anchorregistry` is a trustless Python client for the AnchorRegistry smart contract deployed on Base (Ethereum L2). It reads provenance data directly from on-chain events via RPC — with zero dependency on AnchorRegistry infrastructure.

**The package is fully independent from the AnchorRegistry API, Supabase, or any off-chain system.** An outside developer with only an RPC endpoint and the contract address can reconstruct the entire registry, verify any artifact, and query any tree. This independence is a first-class design constraint, not an afterthought.

**What it is:**
- A trustless on-chain reader for AnchorRegistry provenance data
- The single source of truth for `ARTIFACT_TYPE_MAP` and `READ_ABI` — imported by `ar-api/blockchain.py`
- A reference implementation proving the registry is self-describing and permanently reconstructible

**What it is not:**
- A registration tool (that is a separate future package — `anchorid`)
- A wrapper around the AnchorRegistry API
- An infrastructure-dependent client

---

## 2. Core Design Principles

### 2.1 Zero Infrastructure Dependency
The only inputs required are:
- An Ethereum RPC endpoint (Infura, Alchemy, or self-hosted node)
- The contract address (public on Etherscan forever)
- The deploy block number (documented in `constants.py`)

No API keys. No accounts. No AnchorRegistry servers.

### 2.2 Two-Level Record Structure
Every anchor record returned by any function follows a consistent two-level structure:

```python
{
    # Universal fields — identical schema for every anchor type
    "ar_id": "AR-2026-Pvdp0W5",
    "registered": True,
    "artifact_type_index": 0,
    "artifact_type_name": "CODE",
    "tx": "0xe36116a1406b366c860772fb2a76f6c685cbf05f4a091ef3cb60c1d0da978646",
    "block": 10533679,
    "registrant": "0xc7a7afde1177fbf0bb265ea5a616d1b8d7ed8c44",
    "manifest_hash": "3e2d69872aaeecffb5e6dad0fd8166043f77a29ef67544d5839695a6cdf0da6f",
    "parent_ar_id": "",
    "descriptor": "DeFiPy: Python SDK for DeFi Analytics and Agents",
    "title": "DeFiPy GitHub",
    "author": "Ian Moore",
    "tree_id": "ar-operator-v1",

    # Type-specific fields — only fields belonging to this artifact type
    "data": {
        "git_hash": "18afe3d8ba65ac681791eb1013b57522910244b7",
        "license": "MIT",
        "language": "Python",
        "version": "v1.0.0",
        "url": "https://github.com/defipy-devs/defipy"
    }
}
```

**Design rationale:**
- Universal fields are always flat — safe for DataFrame directly
- `data` dict carries only the fields for the registered type — no None pollution, no semantic ambiguity across types with overlapping field names (`platform`, `format`, `language`, `version`, `institution`)
- Consistent schema regardless of artifact type
- `json.dumps(record)` works without transformation
- New artifact types in future versions add a new `data` shape without changing the universal layer

### 2.3 treeId as the Harvest Key
`treeId` is indexed as topic 3 on the `Anchored` event. This enables targeted tree-level queries via `eth_getLogs` without scanning the full event log. The harvest strategy:

- **Full registry recovery:** get all unique `treeId` topics from the event log → for each treeId pull all anchors → reconstruct parent-child relationships from `parentArId`
- **Single tree recovery:** query `eth_getLogs` filtered by a specific `treeId` topic → reconstruct that tree only
- **Individual anchor:** query by `arId` topic (topic 1) → single event returned

`treeIdPlain` in the non-indexed event data provides the human-readable string needed to reconstruct the topic for querying.

---

## 3. On-Chain Event Structure

The `Anchored` event emitted by `AnchorRegistry.sol`:

```solidity
event Anchored(
    string  indexed arId,         // topic 1 — keccak256 of AR-ID string
    address indexed registrant,   // topic 2 — registrant wallet address
    uint8           artifactType, // non-indexed — decoded from data
    string          arIdPlain,    // non-indexed — human-readable AR-ID
    string          descriptor,   // non-indexed
    string          title,        // non-indexed
    string          author,       // non-indexed
    string          manifestHash, // non-indexed
    string          parentArId,   // non-indexed
    string  indexed treeId,       // topic 3 — keccak256 of treeId string
    string          treeIdPlain   // non-indexed — human-readable treeId
)
```

**Key invariant:** `arIdPlain` and `treeIdPlain` are non-indexed plain string fields. This means full registry reconstruction from event data alone requires no secondary contract calls and no database dependency. The human-readable AR-ID and treeId are always present in the raw log data.

---

## 4. Configuration

### 4.1 Environment Variables

```bash
ANCHOR_REGISTRY_ADDRESS   # contract address — required, no default
BASE_RPC_URL              # RPC endpoint — defaults to public Base RPC
NETWORK                   # "base" | "sepolia" — defaults to "base"
```

Auto-configuration from env vars works without calling `configure()` explicitly. If env vars are set, the package initialises silently on first use.

### 4.2 `configure()` Function

```python
from anchorregistry import configure

configure(
    contract_address="0x...",
    rpc_url="https://mainnet.base.org",
    network="base"
)
```

Explicit configuration overrides env vars. Useful for scripts that manage multiple networks or need to switch between Sepolia and mainnet within the same process.

### 4.3 Network Presets in `constants.py`

```python
NETWORKS = {
    "base": {
        "contract_address": "TBD — mainnet deploy",
        "deploy_block":     None,  # set at mainnet deploy
        "chain_id":         8453,
        "rpc_url":          "https://mainnet.base.org",
    },
    "sepolia": {
        "contract_address": "0x9dAb9f5B754f8C56B5F7BAd3E92A8bDe7317AD29",
        "deploy_block":     None,  # set from testnet deploy record
        "chain_id":         11155111,
        "rpc_url":          "https://rpc.sepolia.org",
    },
}
```

`CONTRACT_ADDRESS` and `DEPLOY_BLOCK` exported at the top level always reflect the active network.

> ⚠️ **Build target:** This package is built and validated against the Sepolia contract (`0x9dAb9f5B754f8C56B5F7BAd3E92A8bDe7317AD29`) only. The current Base mainnet contract is **deprecated** and will be replaced at launch with the right-sized contract. Do not test against or build the ABI around the current mainnet contract. Base mainnet `contract_address` and `deploy_block` in `constants.py` are TBD — populated only at mainnet deploy.

### 4.4 Network-Agnostic Usage

The package works identically against mainnet and Sepolia. Network selection is the only configuration difference. All query functions, record structures, field schemas, and enums are identical across networks.

**Mainnet (default):**
```python
# No configuration needed if env vars are set
from anchorregistry import get_by_arid
record = get_by_arid("AR-2026-Pvdp0W5")
```

**Sepolia:**
```python
from anchorregistry import configure, get_by_arid
configure(network="sepolia")
record = get_by_arid("AR-2026-Pvdp0W5")
```

**Explicit RPC override — works on either network:**
```python
configure(network="sepolia", rpc_url="https://my-own-sepolia-node.com")
record = get_by_arid("AR-2026-Pvdp0W5")
```

**Switching networks within a process:**
```python
configure(network="sepolia")
testnet_records = get_all()

configure(network="base")
mainnet_records = get_all()
```

### 4.5 Configuration Resolution Priority

`config.py` resolves all configuration values in this order, highest priority first:

```
1. Explicit rpc_url parameter on the function call
2. configure() call in the current process
3. Environment variables — ANCHOR_REGISTRY_ADDRESS, BASE_RPC_URL, NETWORK
4. NETWORKS preset for the active network (default: "base")
```

`CONTRACT_ADDRESS` resolution is network-aware: when `network="sepolia"`, it resolves to the Sepolia address from `NETWORKS`. When `network="base"`, it resolves to the mainnet address. An explicit `contract_address` in `configure()` always overrides both.

`DEPLOY_BLOCK` follows the same resolution — network preset value is the default, overridable via `configure()` or env var. This means `get_all()` always scans from the correct starting block for whichever network is active.

---

## 5. Public Interface

### 5.1 Query Functions

```python
from anchorregistry import (
    get_by_arid,
    get_by_registrant,
    get_by_tree,
    get_by_type,
    get_all,
    verify,
    watermark,
    configure,
    to_dataframe,
)
```

#### `get_by_arid(ar_id, rpc_url=None) → dict`
Fetch a single anchor record by AR-ID. Uses the indexed `arId` topic for a targeted single-event query. Raises `AnchorNotFoundError` if AR-ID does not exist on-chain.

```python
record = get_by_arid("AR-2026-Pvdp0W5")
```

#### `get_by_registrant(wallet_address, rpc_url=None) → list[dict]`
Fetch all anchors registered by a specific wallet address. Uses the indexed `registrant` topic.

```python
records = get_by_registrant("0xc7a7afde1177fbf0bb265ea5a616d1b8d7ed8c44")
```

#### `get_by_tree(tree_id_plain, rpc_url=None) → list[dict]`
Fetch all anchors belonging to a specific tree. Uses the indexed `treeId` topic. Returns full tree with parent-child relationships reconstructed from `parentArId`.

```python
records = get_by_tree("ar-operator-v1")
```

#### `get_by_type(artifact_type, rpc_url=None) → list[dict]`
Fetch all anchors of a specific artifact type. Post-filter on decoded `artifactType` field from event data.

```python
from anchorregistry.enums import ArtifactType
records = get_by_type(ArtifactType.CODE)
```

#### `get_all(from_block=None, to_block=None, rpc_url=None) → list[dict]`
Fetch all anchors from the registry. Defaults to scanning from `DEPLOY_BLOCK` to latest. Optional block range for partial harvests.

```python
records = get_all()                              # full registry
records = get_all(from_block=10000000)           # from specific block
records = get_all(from_block=10000000, to_block=10500000)  # block range
```

#### `verify(ar_id, file_path=None, rpc_url=None) → dict`
Fetch anchor record and optionally verify file integrity. If `file_path` is provided, computes SHA256 of the file and compares against `manifest_hash` on-chain. Raises `AnchorNotFoundError` if AR-ID does not exist on-chain.

```python
result = verify("AR-2026-Pvdp0W5")                          # record only
result = verify("AR-2026-Pvdp0W5", file_path="./myfile.py") # + integrity check
# result includes: record + verified (bool) + hash_match (bool)
```

#### `watermark(ar_id, artifact_type=None, rpc_url=None) → str`
Generates the correct SPDX-Anchor or DAPX-Anchor embedded tag for any AR-ID.

- `artifact_type == "CODE"` → `SPDX-Anchor: anchorregistry.ai/{ar_id}`
- All other types → `DAPX-Anchor: anchorregistry.ai/{ar_id}`
- If `artifact_type` is None, resolves via `get_by_arid()` automatically

```python
# With known type — no RPC call needed
line = watermark("AR-2026-Pvdp0W5", artifact_type="CODE")
# → "SPDX-Anchor: anchorregistry.ai/AR-2026-Pvdp0W5"

# Without type — resolves on-chain
line = watermark("AR-2026-Pvdp0W5")
# → "SPDX-Anchor: anchorregistry.ai/AR-2026-Pvdp0W5"

# Non-CODE type
line = watermark("AR-2026-XXXXXX", artifact_type="RESEARCH")
# → "DAPX-Anchor: anchorregistry.ai/AR-2026-XXXXXX"
```

This function is the distribution mechanism baked into the package. Any developer who installs `anchorregistry` can generate the correct embedded tag in one line and drop it into any README, paper footer, or model card.

```python
SOFTWARE_TYPES = {"CODE"}  # SPDX-Anchor applies only to CODE; all others use DAPX-Anchor
```

### 5.2 Analytics Utility

#### `to_dataframe(records) → pd.DataFrame`
Flatten a list of anchor records into a pandas DataFrame. Type-specific fields in `data` are flattened with type-prefixed column names to avoid semantic collision.

```python
from anchorregistry import get_all, to_dataframe

df = to_dataframe(get_all())
df[df.artifact_type_name == "CODE"]
df[df.author == "Ian Moore"]
df.groupby("artifact_type_name").count()
```

Column naming for type-specific fields uses the pattern `{type_name}_{field_name}` — e.g. `code_language`, `text_language`, `data_format`, `media_format` — eliminating ambiguity from fields that share names across types.

### 5.3 Exported Constants

```python
from anchorregistry import ARTIFACT_TYPE_MAP, READ_ABI, CONTRACT_ADDRESS, DEPLOY_BLOCK
```

- `ARTIFACT_TYPE_MAP` — maps type index to type name. Imported by `ar-api/blockchain.py` as single source of truth.
- `READ_ABI` — contract ABI for read operations. Imported by `ar-api/blockchain.py`.
- `CONTRACT_ADDRESS` — deployed contract address on active network.
- `DEPLOY_BLOCK` — block number of contract deployment. Starting point for `get_all()`.

---

## 6. Exceptions

Defined in `exceptions.py`. Outside devs can catch specific errors cleanly.

```python
from anchorregistry.exceptions import AnchorNotFoundError, ConfigurationError
```

#### `AnchorNotFoundError`
Raised by `get_by_arid()`, `verify()`, and `watermark()` (when resolving type) when the AR-ID does not exist on-chain.

```python
try:
    record = get_by_arid("AR-2026-XXXXXXX")
except AnchorNotFoundError:
    print("Anchor not found on-chain")
```

#### `ConfigurationError`
Raised when the package is used before a contract address is available — neither env var nor `configure()` has been called, and no network preset applies.

```python
try:
    configure(contract_address="0x...", network="base")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

---

## 7. Canonical Field Schema

### 7.1 Universal Fields (every anchor)

| Field | Type | Source |
|---|---|---|
| `ar_id` | str | arIdPlain (non-indexed event data) |
| `registered` | bool | derived |
| `artifact_type_index` | int | artifactType (non-indexed) |
| `artifact_type_name` | str | derived from ARTIFACT_TYPE_MAP |
| `tx` | str | transaction hash |
| `block` | int | block number |
| `registrant` | str | registrant (indexed topic 2) |
| `manifest_hash` | str | manifestHash (non-indexed) |
| `parent_ar_id` | str | parentArId (non-indexed) |
| `descriptor` | str | descriptor (non-indexed) |
| `title` | str | title (non-indexed) |
| `author` | str | author (non-indexed) |
| `tree_id` | str | treeIdPlain (non-indexed) |

### 7.2 Type-Specific `data` Fields

**CODE (0)**
```python
{"git_hash", "license", "language", "version", "url"}
```

**RESEARCH (1)**
```python
{"doi", "institution", "co_authors", "url"}
```

**DATA (2)**
```python
{"data_version", "format", "row_count", "schema_url", "url"}
```

**MODEL (3)**
```python
{"model_version", "architecture", "parameters", "training_dataset", "url"}
```

**AGENT (4)**
```python
{"agent_version", "runtime", "capabilities", "url"}
```

**MEDIA (5)**
```python
{"media_type", "platform", "format", "duration", "isrc", "url"}
```

**TEXT (6)**
```python
{"text_type", "isbn", "publisher", "language", "url"}
```

**POST (7)**
```python
{"platform", "post_id", "post_date", "url"}
```

**ONCHAIN (8)**
```python
{"chain_id", "asset_type", "contract_address", "tx_hash", "token_id", "block_number", "url"}
```

**REPORT (9)**
```python
{"report_type", "client", "engagement", "version", "authors", "institution", "url", "file_manifest_hash"}
```

**NOTE (10)**
```python
{"note_type", "date", "participants", "url", "file_manifest_hash"}
```

**WEBSITE (11)**
```python
{"url", "platform", "description"}
```

**EVENT (12)**
```python
{"executor", "event_type", "event_date", "location", "orchestrator", "url"}
```

**RECEIPT (13)**
```python
{"receipt_type", "merchant", "amount", "currency", "order_id", "platform", "url", "file_manifest_hash"}
```

**LEGAL (14)**
```python
{"doc_type", "jurisdiction", "parties", "effective_date", "url"}
```

**ENTITY (15)**
```python
{"entity_type", "entity_domain", "verification_method", "verification_proof", "canonical_url", "document_hash"}
```

**PROOF (16)**
```python
{"proof_type", "proof_system", "circuit_id", "vkey_hash", "audit_firm", "audit_scope", "verifier_url", "report_url", "proof_hash"}
```

**RETRACTION (17)**
```python
{"target_ar_id", "reason", "replaced_by"}
```

**REVIEW (18)**
```python
{"target_ar_id", "review_type", "evidence_url"}
```

**VOID (19)**
```python
{"target_ar_id", "review_ar_id", "finding_url", "evidence"}
```

**AFFIRMED (20)**
```python
{"target_ar_id", "affirmed_by", "finding_url"}
```

**ACCOUNT (21)**
```python
{"capacity"}  # uint256 — only non-string type-specific field
```

**OTHER (22)**
```python
{"kind", "platform", "url", "value", "file_manifest_hash"}
```

---

## 8. Package Structure

```
anchorregistry/
├── anchorregistry/
│   ├── __init__.py          # public API exports
│   ├── client.py            # get_by_arid, get_by_registrant, get_by_tree,
│   │                        # get_by_type, get_all, verify, watermark
│   ├── config.py            # configure(), env var resolution, active network state
│   ├── decoder.py           # raw log → structured two-level record
│   ├── exceptions.py        # AnchorNotFoundError, ConfigurationError
│   ├── types.py             # ARTIFACT_TYPE_MAP, field definitions per type
│   ├── abi.py               # READ_ABI, contract ABI definitions
│   ├── constants.py         # NETWORKS dict, CONTRACT_ADDRESS, DEPLOY_BLOCK
│   ├── rpc.py               # RPC connection, eth_getLogs wrapper
│   ├── utils.py             # to_dataframe(), keccak256 topic builder, helpers
│   │
│   └── enums/
│       ├── __init__.py      # exports all enums
│       ├── artifact_type.py # ArtifactType — 23 types
│       ├── asset_type.py    # OnChain asset types
│       ├── review_type.py   # Review types
│       ├── entity_type.py   # PERSON, COMPANY, INSTITUTION, GOVERNMENT...
│       ├── proof_type.py    # ZK, FORMAL, AUDIT...
│       ├── receipt_type.py  # COMMERCIAL, MEDICAL, FINANCIAL, GOVERNMENT...
│       ├── text_type.py     # BLOG, BOOK, ESSAY, ARTICLE, WHITEPAPER...
│       ├── note_type.py     # MEMO, MEETING, CORRESPONDENCE...
│       └── report_type.py   # CONSULTING, FINANCIAL, ESG, AUDIT...
│
├── tests/
│   ├── test_client.py       # integration tests against Sepolia
│   ├── test_decoder.py      # unit tests — raw log → record
│   ├── test_watermark.py    # watermark() — SPDX vs DAPX routing
│   ├── test_config.py       # configure(), env var resolution
│   └── test_utils.py
│
├── docs/
│   ├── conf.py              # Sphinx config
│   ├── index.rst
│   ├── quickstart.rst       # pip install → first get_by_arid call → output shown
│   ├── api.rst              # autodoc — all public functions
│   └── recover.rst          # trustless reconstruction walkthrough
│
├── pyproject.toml
├── README.md                # DAPX-Anchor tag embedded at publish
└── LICENSE                  # BUSL-1.1
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `client.py` | All public query functions + `watermark()`. The only file outside devs need. |
| `config.py` | `configure()`, env var resolution, active network state. |
| `decoder.py` | Raw log bytes → two-level structured record. Type-aware field mapping. |
| `exceptions.py` | `AnchorNotFoundError`, `ConfigurationError`. Explicit error surface for outside devs. |
| `types.py` | `ARTIFACT_TYPE_MAP`. Imported by `ar-api/blockchain.py`. |
| `abi.py` | `READ_ABI`. Imported by `ar-api/blockchain.py`. |
| `constants.py` | `NETWORKS` dict, `CONTRACT_ADDRESS`, `DEPLOY_BLOCK`, network config. |
| `rpc.py` | RPC connection and `eth_getLogs` wrapper. Isolated — swap RPC layer here. |
| `utils.py` | `to_dataframe()`, topic builder (keccak256), general helpers. |
| `enums/` | Canonical enum definitions for all categorical fields. Self-documenting taxonomy. |

### Internal Dependency Graph

```
enums/          ← no internal dependencies
exceptions.py   ← no internal dependencies
constants.py    ← no internal dependencies
abi.py          ← no internal dependencies
types.py        ← enums/
config.py       ← constants.py, exceptions.py
rpc.py          ← config.py
decoder.py      ← types.py, enums/, abi.py
utils.py        ← enums/
client.py       ← rpc.py, decoder.py, utils.py, exceptions.py
__init__.py     ← client.py, config.py, utils.py, types.py, abi.py, constants.py
```

### `__init__.py` Public Exports

```python
from anchorregistry.client import (
    get_by_arid,
    get_by_registrant,
    get_by_tree,
    get_by_type,
    get_all,
    verify,
    watermark,
)
from anchorregistry.config import configure
from anchorregistry.utils import to_dataframe
from anchorregistry.types import ARTIFACT_TYPE_MAP
from anchorregistry.abi import READ_ABI
from anchorregistry.constants import CONTRACT_ADDRESS, DEPLOY_BLOCK
from anchorregistry.exceptions import AnchorNotFoundError, ConfigurationError
```

---

## 9. Internal Architecture

### 9.1 Core Internal Functions

```python
# config.py
_resolve_config(rpc_url)                    # env var → configure() → parameter, in priority order

# rpc.py
_connect(rpc_url)                           # returns web3 connection
_get_logs(topic, from_block, to_block)      # eth_getLogs wrapper

# utils.py
_build_topic(string)                        # keccak256(string) → topic hash

# decoder.py
_decode_event(raw_log)                      # raw log → two-level record
_decode_data_fields(artifact_type, fields)  # type-aware field mapping → data dict
```

### 9.2 Composition Pattern

Everything composes on `_get_logs` + `_decode_event`:

```
get_by_arid       → _build_topic(ar_id) + _get_logs(topic_1) + _decode_event
get_by_registrant → _get_logs(topic_2=wallet) + _decode_event × N
get_by_tree       → _build_topic(tree_id) + _get_logs(topic_3) + _decode_event × N
get_by_type       → _get_logs(all) + _decode_event × N + filter by artifact_type
get_all           → _get_logs(all, from_block, to_block) + _decode_event × N
verify            → get_by_arid + optional SHA256 comparison
watermark         → optional get_by_arid (type resolution) + tag prefix logic
```

`_decode_event` is the critical function. If it is correct — proper ABI decoding, correct topic construction, correct field mapping by artifact type — everything else follows.

---

## 10. Dependencies

```toml
dependencies = [
    "web3>=6.0",
]

[project.optional-dependencies]
analytics = ["pandas"]
```

Keep it minimal. `pandas` is optional — only required for `to_dataframe()`. Import error message is explicit if user calls `to_dataframe()` without pandas installed.

---

## 11. ReadTheDocs

Hosted at: `anchorregistry.readthedocs.io`

### 11.1 Pages

| Page | Content |
|---|---|
| Quickstart | `pip install anchorregistry` → `get_by_arid` → output shown. Under 10 lines. |
| API Reference | Autodoc from docstrings. All public functions, parameters, return types, exceptions. |
| Recover Walkthrough | Full registry reconstruction step by step. No API key. No account. The trust proof. |
| Contract Reference | Address, deploy block, network, Etherscan link. |

### 11.2 Lead Statement
The docs lead with: **no API key, no account, no dependency on AnchorRegistry infrastructure.** Just an RPC endpoint and the contract address.

---

## 12. Build & Test Sequencing

### 12.1 Pre-Mainnet (Sepolia)

Build and validate against Sepolia testnet before mainnet launch. The DeFiPy ecosystem tree anchored during QA is the primary test dataset — a non-trivial tree covering CODE, WEBSITE, POST, TEXT artifact types with real parent-child relationships.

> ⚠️ **Sepolia only.** The current Base mainnet contract is deprecated and will be replaced at launch. All development and testing targets Sepolia exclusively until the new mainnet contract is deployed. Never test against the current mainnet contract — it has the old taxonomy and old event signature.

```python
TEST_CONTRACT = "0x9dAb9f5B754f8C56B5F7BAd3E92A8bDe7317AD29"
TEST_RPC      = os.environ.get("SEPOLIA_RPC_URL")
TEST_AR_ID    = "AR-2026-Pvdp0W5"   # known DeFiPy root anchor from QA sprint
```

| Step | Action |
|---|---|
| 1 | Build package against Sepolia — `configure(contract_address=TEST_CONTRACT, network="sepolia")` |
| 2 | `get_by_arid` — validate two-level record output for each artifact type present |
| 3 | `get_by_tree` — validate full DeFiPy tree reconstruction from `treeIdPlain` |
| 4 | `get_by_registrant` — validate all DeFiPy anchors returned for operator wallet |
| 5 | `get_by_type` — validate CODE, WEBSITE, POST, TEXT type filters |
| 6 | `get_all` — run full Sepolia registry harvest, validate output |
| 7 | `verify` — validate AR-ID resolution + optional SHA256 file comparison |
| 8 | `watermark` — validate SPDX-Anchor for CODE, DAPX-Anchor for all other types present |
| 9 | `to_dataframe` — validate flat DataFrame output, column naming, no alignment issues |
| 10 | `AnchorNotFoundError` — validate raised for nonexistent AR-ID |
| 11 | Fix any field mapping or decoding issues surfaced |

### 12.2 Post-Mainnet

| Step | Action |
|---|---|
| 1 | Mainnet deploy — `CONTRACT_ADDRESS` and `DEPLOY_BLOCK` updated in `constants.py` |
| 2 | Retest all query functions against mainnet genesis anchor |
| 3 | Publish to PyPI |
| 4 | Update `ar-api/blockchain.py` to import `ARTIFACT_TYPE_MAP` and `READ_ABI` from package |
| 5 | Embed `DAPX-Anchor` tag in `README.md` pointing to package's own AR-ID |
| 6 | ReadTheDocs live |

---

## 13. ar-api Integration

After PyPI publication, `ar-api/blockchain.py` is updated to import directly from the package:

```python
from anchorregistry import ARTIFACT_TYPE_MAP, READ_ABI, CONTRACT_ADDRESS, DEPLOY_BLOCK
```

This eliminates drift between the package and the API — type ordering and ABI are defined once, in one place, and both systems consume from that single source of truth. Any future type additions or ABI changes are made in the package and automatically reflected in the API on next deploy.

---

## 14. Out of Scope for V1

- Write operations (registration) — production only, never in this package
- Tree traversal helpers (walk parent/child chain) — V2
- Batch verification — V2
- Async interface — V2
- CLI tool — separate `anchorid` package, separate concern

---

## 15. Notes

- `anchorid` remains the reserved PyPI name for a future user-facing registration CLI — separate package, separate concern
- Patent figures reflect an earlier 18-type taxonomy (immutable as filed). This 23-type taxonomy is the source of truth for all non-patent documents
- BUSL-1.1 applies at publish. Change date March 12, 2028 → Apache-2.0
- `DAPX-Anchor: anchorregistry.ai/[AR-ID]` tag embedded in `README.md` at publish — the package anchors itself

---

*AnchorRegistry™ · anchorregistry.com · anchorregistry.ai · March 2026*
