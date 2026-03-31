# SPDX-License-Identifier: BUSL-1.1
"""ARTIFACT_TYPE_MAP and per-type field definitions.

ARTIFACT_TYPE_MAP is the single source of truth for type index → name mapping.
Imported by ar-api/blockchain.py.
"""

from anchorregistry.enums import ArtifactType

# Index → name mapping for all 23 artifact types
ARTIFACT_TYPE_MAP: dict[int, str] = {t.value: t.name for t in ArtifactType}

# Type-specific data field names (snake_case), keyed by ArtifactType value.
# Used by decoder.py to map ABI-decoded extra bytes → data dict.
TYPE_FIELDS: dict[int, tuple[str, ...]] = {
    ArtifactType.CODE.value:       ("git_hash", "license", "language", "version", "url"),
    ArtifactType.RESEARCH.value:   ("doi", "institution", "co_authors", "url"),
    ArtifactType.DATA.value:       ("data_version", "format", "row_count", "schema_url", "url"),
    ArtifactType.MODEL.value:      ("model_version", "architecture", "parameters", "training_dataset", "url"),
    ArtifactType.AGENT.value:      ("agent_version", "runtime", "capabilities", "url"),
    ArtifactType.MEDIA.value:      ("media_type", "platform", "format", "duration", "isrc", "url"),
    ArtifactType.TEXT.value:       ("text_type", "isbn", "publisher", "language", "url"),
    ArtifactType.POST.value:       ("platform", "post_id", "post_date", "url"),
    ArtifactType.ONCHAIN.value:    ("chain_id", "asset_type", "contract_address", "tx_hash", "token_id", "block_number", "url"),
    ArtifactType.REPORT.value:     ("report_type", "client", "engagement", "version", "authors", "institution", "url", "file_manifest_hash"),
    ArtifactType.NOTE.value:       ("note_type", "date", "participants", "url", "file_manifest_hash"),
    ArtifactType.WEBSITE.value:    ("url", "platform", "description"),
    ArtifactType.EVENT.value:      ("executor", "event_type", "event_date", "location", "orchestrator", "url"),
    ArtifactType.RECEIPT.value:    ("receipt_type", "merchant", "amount", "currency", "order_id", "platform", "url", "file_manifest_hash"),
    ArtifactType.LEGAL.value:      ("doc_type", "jurisdiction", "parties", "effective_date", "url"),
    ArtifactType.ENTITY.value:     ("entity_type", "entity_domain", "verification_method", "verification_proof", "canonical_url", "document_hash"),
    ArtifactType.PROOF.value:      ("proof_type", "proof_system", "circuit_id", "vkey_hash", "audit_firm", "audit_scope", "verifier_url", "report_url", "proof_hash"),
    ArtifactType.RETRACTION.value: ("reason", "replaced_by"),
    ArtifactType.REVIEW.value:     ("review_type", "evidence_url"),
    ArtifactType.VOID.value:       ("review_ar_id", "finding_url", "evidence"),
    ArtifactType.AFFIRMED.value:   ("affirmed_by", "finding_url"),
    ArtifactType.ACCOUNT.value:    ("capacity",),
    ArtifactType.OTHER.value:      ("kind", "platform", "url", "value", "file_manifest_hash"),
}

# ABI type tuples for decoding extra bytes per artifact type.
# Most fields are strings; ACCOUNT.capacity is uint256.
TYPE_ABI: dict[int, tuple[str, ...]] = {
    k: tuple("uint256" if f == "capacity" else "string" for f in fields)
    for k, fields in TYPE_FIELDS.items()
}
