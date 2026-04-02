# SPDX-License-Identifier: BUSL-1.1
"""Unit tests for decoder.py — raw log → two-level record."""

import pytest
from eth_abi import encode
from hexbytes import HexBytes
from web3 import Web3

from anchorregistry.decoder import _decode_data_fields, _decode_event
from anchorregistry.enums import ArtifactType


def _make_raw_log(
    ar_id="AR-2026-TEST01",
    registrant="0xc7a7afde1177fbf0bb265ea5a616d1b8d7ed8c44",
    artifact_type=0,
    descriptor="Test descriptor",
    title="Test Title",
    author="Test Author",
    manifest_hash="abcdef1234567890",
    parent_ar_id="",
    tree_id="ar-operator-v1",
    token_commitment=b"\x00" * 32,
    block_number=12345,
    tx_hash="aa" * 32,
):
    """Build a mock raw log matching the Anchored event structure."""
    event_sig = Web3.keccak(
        text="Anchored(string,address,uint8,string,string,string,string,string,string,string,string,bytes32)"
    )
    ar_id_topic = Web3.keccak(text=ar_id)
    registrant_topic = HexBytes(bytes.fromhex(registrant[2:].rjust(64, "0")))
    tree_id_topic = Web3.keccak(text=tree_id)

    data = encode(
        ["uint8", "string", "string", "string", "string", "string", "string", "string", "bytes32"],
        [artifact_type, ar_id, descriptor, title, author, manifest_hash, parent_ar_id, tree_id, token_commitment],
    )

    return {
        "topics": [event_sig, ar_id_topic, registrant_topic, tree_id_topic],
        "data": HexBytes(data),
        "blockNumber": block_number,
        "transactionHash": HexBytes(bytes.fromhex(tx_hash)),
    }


class TestDecodeEvent:
    """Tests for _decode_event()."""

    def test_decodes_code_anchor(self):
        log = _make_raw_log(
            ar_id="AR-2026-CODE01",
            artifact_type=ArtifactType.CODE,
            title="My Code",
            author="Alice",
        )
        record = _decode_event(log)
        assert record["ar_id"] == "AR-2026-CODE01"
        assert record["artifact_type_index"] == 0
        assert record["artifact_type_name"] == "CODE"
        assert record["title"] == "My Code"
        assert record["author"] == "Alice"
        assert record["registered"] is True
        assert record["data"] == {}

    def test_decodes_research_anchor(self):
        log = _make_raw_log(
            ar_id="AR-2026-RES01",
            artifact_type=ArtifactType.RESEARCH,
            descriptor="Research paper",
        )
        record = _decode_event(log)
        assert record["artifact_type_name"] == "RESEARCH"
        assert record["descriptor"] == "Research paper"

    def test_decodes_registrant_address(self):
        log = _make_raw_log(registrant="0xabcdef1234567890abcdef1234567890abcdef12")
        record = _decode_event(log)
        assert record["registrant"] == "0xabcdef1234567890abcdef1234567890abcdef12"

    def test_decodes_block_and_tx(self):
        log = _make_raw_log(block_number=99999, tx_hash="bb" * 32)
        record = _decode_event(log)
        assert record["block"] == 99999
        assert record["tx"] == "0x" + "bb" * 32

    def test_decodes_parent_ar_id(self):
        log = _make_raw_log(parent_ar_id="AR-2026-PARENT")
        record = _decode_event(log)
        assert record["parent_ar_id"] == "AR-2026-PARENT"

    def test_decodes_tree_id(self):
        log = _make_raw_log(tree_id="my-custom-tree")
        record = _decode_event(log)
        assert record["tree_id"] == "my-custom-tree"

    def test_decodes_token_commitment(self):
        tc = bytes.fromhex("ab" * 32)
        log = _make_raw_log(token_commitment=tc)
        record = _decode_event(log)
        assert record["token_commitment"] == "0x" + "ab" * 32

    def test_decodes_zero_token_commitment(self):
        log = _make_raw_log(token_commitment=b"\x00" * 32)
        record = _decode_event(log)
        assert record["token_commitment"] == "0x" + "00" * 32

    def test_decodes_all_artifact_types(self):
        for t in ArtifactType:
            log = _make_raw_log(artifact_type=t.value)
            record = _decode_event(log)
            assert record["artifact_type_index"] == t.value
            assert record["artifact_type_name"] == t.name


class TestDecodeDataFields:
    """Tests for _decode_data_fields()."""

    def test_code_fields(self):
        extra = encode(
            ["string", "string", "string", "string", "string"],
            ["abc123", "MIT", "Python", "v1.0.0", "https://github.com/example"],
        )
        data = _decode_data_fields(ArtifactType.CODE, extra)
        assert data["git_hash"] == "abc123"
        assert data["license"] == "MIT"
        assert data["language"] == "Python"
        assert data["version"] == "v1.0.0"
        assert data["url"] == "https://github.com/example"

    def test_research_fields(self):
        extra = encode(
            ["string", "string", "string", "string"],
            ["10.1234/test", "MIT", "Alice, Bob", "https://arxiv.org/123"],
        )
        data = _decode_data_fields(ArtifactType.RESEARCH, extra)
        assert data["doi"] == "10.1234/test"
        assert data["institution"] == "MIT"
        assert data["co_authors"] == "Alice, Bob"

    def test_account_capacity_uint256(self):
        extra = encode(["uint256"], [100])
        data = _decode_data_fields(ArtifactType.ACCOUNT, extra)
        assert data["capacity"] == 100
        assert isinstance(data["capacity"], int)

    def test_website_fields(self):
        extra = encode(
            ["string", "string", "string"],
            ["https://example.com", "Next.js", "A website"],
        )
        data = _decode_data_fields(ArtifactType.WEBSITE, extra)
        assert data["url"] == "https://example.com"
        assert data["platform"] == "Next.js"
        assert data["description"] == "A website"

    def test_retraction_fields(self):
        extra = encode(["string", "string"], ["Outdated", "AR-2026-NEW"])
        data = _decode_data_fields(ArtifactType.RETRACTION, extra)
        assert data["reason"] == "Outdated"
        assert data["replaced_by"] == "AR-2026-NEW"

    def test_empty_bytes_returns_empty_dict(self):
        data = _decode_data_fields(ArtifactType.CODE, b"")
        assert data == {}

    def test_unknown_type_returns_empty_dict(self):
        data = _decode_data_fields(999, b"\x00" * 32)
        assert data == {}
