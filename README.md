# anchorregistry

**Read-only Python client for the Anchor Registry provenance chain.**

`anchorregistry` is the canonical Python interface to [Anchor Registry](https://anchorregistry.com) — a blockchain-based provenance registry built on Base (Ethereum L2). It is the same library used in Anchor Registry's own production backend.

Verify what existed, when, and who registered it — directly from the chain.

**SPDX-Anchor: [anchorregistry.ai/AR-2026-0000001](https://anchorregistry.ai/AR-2026-0000001)**

---

## How it works

Creators register artifacts through [anchorregistry.com](https://anchorregistry.com) and receive an immutable **AR-ID** — an on-chain anchor encoding the artifact's content hash, timestamp, and registrant. This package queries those records directly from the Base blockchain — no intermediary API.

No API key. No account. Read-only.

---

## Installation

```bash
pip install anchorregistry
```

Requires Python 3.11+

---

## Usage

```python
from anchorregistry import verify, lookup, watermark

# Confirm an AR-ID is valid and exists on-chain
verify("AR-0x...")

# Fetch the full provenance record for an AR-ID
record = lookup("AR-0x...")

# Generate a watermark line to embed in your artifact
line = watermark("AR-0x...")
# SPDX-Anchor: AR-0x... @ anchorregistry.com   (software artifacts)
# DAPX-Anchor: AR-0x... @ anchorregistry.com   (all other artifacts)
```

---

## Watermark Standards

Anchor Registry defines two watermark standards for embedding a provenance signal directly in your artifact:

**SPDX-Anchor** — for software (code, packages, repositories)
```
SPDX-Anchor: AR-<id> @ anchorregistry.com
```

**DAPX-Anchor** — for all other artifacts (research, data, models, media, legal, proofs)
```
DAPX-Anchor: AR-<id> @ anchorregistry.com
```

One line signals membership in a provenance tree — queryable by humans and AI agents alike.

---

## Design

- **Read-only.** Registration happens through anchorregistry.com. This package only reads.
- **No auth required.** Verification is open and free to anyone.
- **Production parity.** This is the same library powering the Anchor Registry backend — not a separate wrapper.
- **Built on Base.** Queries resolve directly against the Base L2 chain. Base settles to Ethereum mainnet — provenance anchors inherit Ethereum-grade finality.

---

## Status

> Pre-release. Core library under active development. API surface is not yet stable.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE)

---

## Links

- Website: [anchorregistry.com](https://anchorregistry.com)
- PyPI: [pypi.org/project/anchorregistry](https://pypi.org/project/anchorregistry)
- Source: [github.com/anchorregistry/ar-python](https://github.com/anchorregistry/ar-python)
