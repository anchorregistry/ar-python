# SPDX-License-Identifier: BUSL-1.1
"""Canonical READ_ABI for the AnchorRegistry contract.

Sourced from the verified Sepolia deployment. Imported by ar-api/blockchain.py
as the single source of truth.
"""

READ_ABI = [
    # ── Anchored event ────────────────────────────────────────────────
    {
        "anonymous": False,
        "name": "Anchored",
        "type": "event",
        "inputs": [
            {"indexed": True,  "internalType": "string",            "name": "arId",         "type": "string"},
            {"indexed": True,  "internalType": "address",           "name": "registrant",   "type": "address"},
            {"indexed": False, "internalType": "enum ArtifactType", "name": "artifactType", "type": "uint8"},
            {"indexed": False, "internalType": "string",            "name": "arIdPlain",    "type": "string"},
            {"indexed": False, "internalType": "string",            "name": "descriptor",   "type": "string"},
            {"indexed": False, "internalType": "string",            "name": "title",        "type": "string"},
            {"indexed": False, "internalType": "string",            "name": "author",       "type": "string"},
            {"indexed": False, "internalType": "string",            "name": "manifestHash", "type": "string"},
            {"indexed": False, "internalType": "string",            "name": "parentArId",   "type": "string"},
            {"indexed": True,  "internalType": "string",            "name": "treeId",       "type": "string"},
            {"indexed": False, "internalType": "string",            "name": "treeIdPlain",      "type": "string"},
            {"indexed": False, "internalType": "bytes32",           "name": "tokenCommitment",  "type": "bytes32"},
        ],
    },
    # ── Sealed event ───────────────────────────────────────────────────
    {
        "anonymous": False,
        "name": "Sealed",
        "type": "event",
        "inputs": [
            {"indexed": True,  "internalType": "string",  "name": "arId",            "type": "string"},
            {"indexed": False, "internalType": "string",  "name": "newTreeRoot",      "type": "string"},
            {"indexed": False, "internalType": "string",  "name": "reason",           "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "sealedAtBlock",    "type": "uint256"},
            {"indexed": False, "internalType": "bytes32", "name": "tokenCommitment",  "type": "bytes32"},
        ],
    },
    # ── isSealed(arId) → bool ────────────────────────────────────────
    {
        "type": "function",
        "name": "isSealed",
        "stateMutability": "view",
        "inputs":  [{"internalType": "string", "name": "", "type": "string"}],
        "outputs": [{"internalType": "bool",   "name": "", "type": "bool"}],
    },
    # ── sealContinuation(arId) → string ──────────────────────────────
    {
        "type": "function",
        "name": "sealContinuation",
        "stateMutability": "view",
        "inputs":  [{"internalType": "string", "name": "", "type": "string"}],
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
    },
    # ── registered(arId) → bool ───────────────────────────────────────
    {
        "type": "function",
        "name": "registered",
        "stateMutability": "view",
        "inputs":  [{"internalType": "string", "name": "", "type": "string"}],
        "outputs": [{"internalType": "bool",   "name": "", "type": "bool"}],
    },
    # ── getAnchorData(arId) → bytes ───────────────────────────────────
    {
        "type": "function",
        "name": "getAnchorData",
        "stateMutability": "view",
        "inputs":  [{"internalType": "string", "name": "arId", "type": "string"}],
        "outputs": [{"internalType": "bytes",  "name": "",     "type": "bytes"}],
    },
    # ── anchorTypes(arId) → uint8 ─────────────────────────────────────
    {
        "type": "function",
        "name": "anchorTypes",
        "stateMutability": "view",
        "inputs":  [{"internalType": "string",  "name": "",  "type": "string"}],
        "outputs": [{"internalType": "uint8",   "name": "",  "type": "uint8"}],
    },
]
