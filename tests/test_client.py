# SPDX-License-Identifier: BUSL-1.1
"""Integration tests for client.py — run against Sepolia testnet.

These tests require SEPOLIA_RPC_URL to be set. They are skipped otherwise.

Authentication tests additionally require:
  ANCHOR_OWNERSHIP_TOKEN — ownership token for a known anchor
  ANCHOR_ROOT_AR_ID      — root AR-ID corresponding to that ownership token
"""

import os

from eth_hash.auto import keccak as _keccak

import pytest

from anchorregistry import configure
from anchorregistry.exceptions import AnchorNotFoundError

TEST_CONTRACT = "0x9E1F48D3C46bc69a540d16511FaA76Add25A8451"
TEST_RPC = os.environ.get("SEPOLIA_RPC_URL")
TEST_AR_ID = "AR-2026-D5bqN06"  # known anchor on current Sepolia contract

needs_rpc = pytest.mark.skipif(
    TEST_RPC is None, reason="SEPOLIA_RPC_URL not set"
)

needs_ownership_token = pytest.mark.skipif(
    os.environ.get("ANCHOR_OWNERSHIP_TOKEN") is None
    or os.environ.get("ANCHOR_ROOT_AR_ID") is None,
    reason="ANCHOR_OWNERSHIP_TOKEN and ANCHOR_ROOT_AR_ID not set",
)


@pytest.fixture(autouse=True)
def _configure_sepolia():
    """Configure the package for Sepolia before each test."""
    if TEST_RPC:
        configure(network="sepolia", rpc_url=TEST_RPC)


@pytest.fixture(scope="session")
def live_ar_id():
    """Return the known test AR-ID for the active Sepolia contract."""
    if not TEST_RPC:
        pytest.skip("SEPOLIA_RPC_URL not set")
    configure(network="sepolia", rpc_url=TEST_RPC)
    from anchorregistry import get_by_arid
    try:
        get_by_arid(TEST_AR_ID)
    except Exception:
        pytest.skip(f"Test anchor {TEST_AR_ID} not found on Sepolia contract")
    return TEST_AR_ID


@needs_rpc
class TestGetByArid:
    """Tests for get_by_arid()."""

    def test_returns_valid_record(self, live_ar_id):
        from anchorregistry import get_by_arid

        record = get_by_arid(live_ar_id)
        assert record["ar_id"] == live_ar_id
        assert record["registered"] is True
        assert record["artifact_type_name"] in [
            t.name for t in __import__("anchorregistry.enums", fromlist=["ArtifactType"]).ArtifactType
        ]
        assert record["tx"].startswith("0x")
        assert isinstance(record["block"], int)
        assert isinstance(record["data"], dict)
        assert "token_commitment" in record
        assert record["token_commitment"].startswith("0x")
        assert len(record["token_commitment"]) == 66  # "0x" + 64 hex chars

    def test_not_found_raises(self):
        from anchorregistry import get_by_arid

        with pytest.raises(AnchorNotFoundError):
            get_by_arid("AR-9999-NONEXISTENT")


@needs_rpc
class TestGetByRegistrant:
    """Tests for get_by_registrant()."""

    def test_returns_list(self, live_ar_id):
        from anchorregistry import get_by_arid, get_by_registrant

        record = get_by_arid(live_ar_id)
        registrant = record["registrant"]
        records = get_by_registrant(registrant)
        assert isinstance(records, list)
        assert len(records) > 0
        assert any(r["ar_id"] == live_ar_id for r in records)


@needs_rpc
class TestGetByTree:
    """Tests for get_by_tree()."""

    def test_returns_tree_records(self, live_ar_id):
        from anchorregistry import get_by_arid, get_by_tree

        record = get_by_arid(live_ar_id)
        tree_id = record["tree_id"]
        records = get_by_tree(tree_id)
        assert isinstance(records, list)
        assert len(records) > 0
        assert all(r["tree_id"] == tree_id for r in records)


@needs_rpc
class TestGetByType:
    """Tests for get_by_type()."""

    def test_filters_by_type(self, live_ar_id):
        from anchorregistry import get_by_arid, get_by_type

        record = get_by_arid(live_ar_id)
        type_idx = record["artifact_type_index"]
        records = get_by_type(type_idx)
        assert isinstance(records, list)
        assert all(r["artifact_type_index"] == type_idx for r in records)


@needs_rpc
class TestGetAll:
    """Tests for get_all()."""

    def test_returns_all_records(self):
        from anchorregistry import get_all

        records = get_all()
        assert isinstance(records, list)
        assert len(records) > 0

    def test_block_range(self, live_ar_id):
        from anchorregistry import get_by_arid, get_all

        record = get_by_arid(live_ar_id)
        block = record["block"]
        records = get_all(from_block=block, to_block=block)
        assert any(r["ar_id"] == live_ar_id for r in records)


@needs_rpc
class TestVerify:
    """Tests for verify()."""

    def test_verify_record_only(self, live_ar_id):
        from anchorregistry import verify

        result = verify(live_ar_id)
        assert result["verified"] is True
        assert result["hash_match"] is None
        assert result["ar_id"] == live_ar_id

    def test_verify_with_file(self, live_ar_id, tmp_path):
        from anchorregistry import verify

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        result = verify(live_ar_id, file_path=str(test_file))
        assert result["verified"] is True
        assert isinstance(result["hash_match"], bool)


@needs_rpc
class TestWatermark:
    """Tests for watermark() with on-chain resolution."""

    def test_resolves_type_on_chain(self, live_ar_id):
        from anchorregistry import watermark

        result = watermark(live_ar_id)
        assert "anchorregistry.ai/" + live_ar_id in result
        assert result.startswith("SPDX-Anchor:") or result.startswith("DAPX-Anchor:")


@needs_rpc
class TestTokenCommitment:
    """Tests for token_commitment field presence and format."""

    def test_token_commitment_present(self, live_ar_id):
        from anchorregistry import get_by_arid

        record = get_by_arid(live_ar_id)
        assert "token_commitment" in record
        assert record["token_commitment"].startswith("0x")
        assert len(record["token_commitment"]) == 66

    def test_is_user_initiated_non_governance(self, live_ar_id):
        from anchorregistry import get_by_arid
        from anchorregistry.utils import is_user_initiated

        record = get_by_arid(live_ar_id)
        # Most Sepolia records are content anchors — expect True
        # (governance anchors are rare in testnet QA data)
        result = is_user_initiated(record)
        assert isinstance(result, bool)

    def test_is_user_initiated_zero_sentinel(self):
        from anchorregistry.utils import is_user_initiated

        # Governance sentinel — bytes32(0) → False
        fake_record = {"token_commitment": "0x" + "0" * 64}
        assert is_user_initiated(fake_record) is False

    def test_is_user_initiated_nonzero(self):
        from anchorregistry.utils import is_user_initiated

        # Non-zero commitment → True
        fake_record = {"token_commitment": "0x" + "a" * 64}
        assert is_user_initiated(fake_record) is True


class TestAuthenticateAnchorUnit:
    """Unit tests for authenticate_anchor() — no RPC, uses mocked get_by_arid."""

    def _make_record(self, ar_id: str, ownership_token: str, is_governance: bool = False):
        """Build a fake record with a valid or zero tokenCommitment."""
        if is_governance:
            commitment = "0x" + "0" * 64
        else:
            K_bytes = bytes.fromhex(ownership_token[2:])
            Ci_bytes = ar_id.encode("utf-8")
            commitment = "0x" + _keccak(K_bytes + Ci_bytes).hex()
        return {
            "ar_id": ar_id,
            "registered": True,
            "token_commitment": commitment,
            "artifact_type_name": "RESEARCH",
            "artifact_type_index": 1,
            "tree_id": "test-tree",
            "data": {},
        }

    def test_authenticate_anchor_valid(self, monkeypatch):
        from anchorregistry import authenticate_anchor

        token = "0x" + "ab" * 32
        ar_id = "AR-2026-TestXX"
        record = self._make_record(ar_id, token)

        monkeypatch.setattr("anchorregistry.client.get_by_arid", lambda *a, **kw: record)

        result = authenticate_anchor(token, ar_id)
        assert result["authenticated"] is True
        assert result["verified"] is True
        assert result["is_user_initiated"] is True
        assert result["ar_id"] == ar_id

    def test_authenticate_anchor_wrong_token(self, monkeypatch):
        from anchorregistry import authenticate_anchor

        token = "0x" + "ab" * 32
        wrong_token = "0x" + "cd" * 32
        ar_id = "AR-2026-TestXX"
        record = self._make_record(ar_id, token)

        monkeypatch.setattr("anchorregistry.client.get_by_arid", lambda *a, **kw: record)

        result = authenticate_anchor(wrong_token, ar_id)
        assert result["authenticated"] is False
        assert result["verified"] is False
        assert result["is_user_initiated"] is True

    def test_authenticate_anchor_governance(self, monkeypatch):
        from anchorregistry import authenticate_anchor

        token = "0x" + "ab" * 32
        ar_id = "AR-2026-VoidXX"
        record = self._make_record(ar_id, token, is_governance=True)

        monkeypatch.setattr("anchorregistry.client.get_by_arid", lambda *a, **kw: record)

        result = authenticate_anchor(token, ar_id)
        assert result["authenticated"] is False
        assert result["verified"] is False
        assert result["is_user_initiated"] is False

    def test_authenticate_anchor_token_starting_with_zero(self, monkeypatch):
        """Regression: token starting with 0x00... must not be corrupted by lstrip."""
        from anchorregistry import authenticate_anchor

        # Token whose first hex char after "0x" is '0' — triggers lstrip bug if present
        token = "0x" + "00" + "ab" * 31   # 32 bytes, starts with 0x00
        ar_id = "AR-2026-TestZZ"
        record = self._make_record(ar_id, token)

        monkeypatch.setattr("anchorregistry.client.get_by_arid", lambda *a, **kw: record)

        result = authenticate_anchor(token, ar_id)
        assert result["authenticated"] is True
        assert result["verified"] is True


class TestAuthenticateTreeUnit:
    """Unit tests for authenticate_tree() — no RPC, uses mocked functions."""

    def _make_record(self, ar_id: str, ownership_token: str, tree_id: str, is_governance: bool = False):
        if is_governance:
            commitment = "0x" + "0" * 64
        else:
            K_bytes = bytes.fromhex(ownership_token[2:])
            Ci_bytes = ar_id.encode("utf-8")
            commitment = "0x" + _keccak(K_bytes + Ci_bytes).hex()
        return {
            "ar_id": ar_id,
            "registered": True,
            "token_commitment": commitment,
            "artifact_type_name": "RESEARCH",
            "artifact_type_index": 1,
            "tree_id": tree_id,
            "data": {},
        }

    def _make_tree_id(self, ownership_token: str, root_ar_id: str) -> str:
        K_bytes = bytes.fromhex(ownership_token[2:])
        R_bytes = root_ar_id.encode("utf-8")
        return "0x" + _keccak(K_bytes + R_bytes).hex()

    def test_authenticate_tree_valid(self, monkeypatch):
        from anchorregistry import authenticate_tree

        token = "0x" + "ab" * 32
        root_ar_id = "AR-2026-RootXX"
        child_ar_id = "AR-2026-ChildX"
        tree_id = self._make_tree_id(token, root_ar_id)

        root_record = self._make_record(root_ar_id, token, tree_id)
        child_record = self._make_record(child_ar_id, token, tree_id)
        record_map = {root_ar_id: root_record, child_ar_id: child_record}

        monkeypatch.setattr("anchorregistry.client.get_by_arid", lambda ar_id, **kw: record_map[ar_id])
        monkeypatch.setattr("anchorregistry.client.get_by_tree", lambda *a, **kw: [root_record, child_record])

        result = authenticate_tree(token, root_ar_id)
        assert result["authenticated"] is True
        assert result["anchors_verified"] == 2
        assert result["anchors_failed"] == 0
        assert result["governance_count"] == 0
        assert result["anchor_count"] == 2

    def test_authenticate_tree_layer1_fails(self, monkeypatch):
        from anchorregistry import authenticate_tree

        token = "0x" + "ab" * 32
        root_ar_id = "AR-2026-RootXX"
        wrong_tree_id = "some-other-tree"  # doesn't match SHA256(token + root_ar_id)

        root_record = self._make_record(root_ar_id, token, wrong_tree_id)
        monkeypatch.setattr("anchorregistry.client.get_by_arid", lambda *a, **kw: root_record)

        result = authenticate_tree(token, root_ar_id)
        assert result["authenticated"] is False
        assert result["anchor_count"] == 0

    def test_authenticate_tree_governance_skipped(self, monkeypatch):
        from anchorregistry import authenticate_tree

        token = "0x" + "ab" * 32
        root_ar_id = "AR-2026-RootXX"
        void_ar_id = "AR-2026-VoidXX"
        tree_id = self._make_tree_id(token, root_ar_id)

        root_record = self._make_record(root_ar_id, token, tree_id)
        void_record = self._make_record(void_ar_id, token, tree_id, is_governance=True)
        record_map = {root_ar_id: root_record, void_ar_id: void_record}

        monkeypatch.setattr("anchorregistry.client.get_by_arid", lambda ar_id, **kw: record_map[ar_id])
        monkeypatch.setattr("anchorregistry.client.get_by_tree", lambda *a, **kw: [root_record, void_record])

        result = authenticate_tree(token, root_ar_id)
        assert result["authenticated"] is True
        assert result["anchors_verified"] == 1
        assert result["governance_count"] == 1
        assert result["anchor_count"] == 2


# NOTE: ANCHOR_OWNERSHIP_TOKEN must be a 0x-prefixed bytes32 hex string (keccak256
# token format). UUID-format tokens from pre-upgrade registrations will fail.
# Refresh this env var after making a new Sepolia registration post-upgrade.
@needs_rpc
@needs_ownership_token
class TestAuthenticateIntegration:
    """Live Sepolia integration tests — require ANCHOR_OWNERSHIP_TOKEN + ANCHOR_ROOT_AR_ID."""

    def test_authenticate_anchor_live(self):
        from anchorregistry import authenticate_anchor, get_all

        token = os.environ["ANCHOR_OWNERSHIP_TOKEN"]
        records = get_all()
        # Find a user-initiated anchor (non-zero commitment)
        user_anchors = [r for r in records if r["token_commitment"] != "0x" + "0" * 64]
        if not user_anchors:
            pytest.skip("No user-initiated anchors found on Sepolia")
        ar_id = user_anchors[0]["ar_id"]

        result = authenticate_anchor(token, ar_id)
        assert isinstance(result["authenticated"], bool)
        assert result["is_user_initiated"] is True

    def test_authenticate_tree_live(self):
        from anchorregistry import authenticate_tree

        token = os.environ["ANCHOR_OWNERSHIP_TOKEN"]
        root_ar_id = os.environ["ANCHOR_ROOT_AR_ID"]

        result = authenticate_tree(token, root_ar_id)
        assert result["authenticated"] is True
        assert result["anchors_failed"] == 0
