"""Phase 5A Extraction Layer interfaces and data structures.

Technical Design v1.5 references:
  * s3.1  Source Adapter - SourceDocument / SourceSnapshot with ID, content hash,
          retrieval timestamp, URI.
  * s3.2  Extraction Layer - RawExtraction with candidate value, raw text, page,
          section, extraction method, confidence.
  * s15   Extraction Architecture - TOC / heading detection -> section -> table ->
          candidate fields -> evidence attachment -> canonical input -> validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

from ..canonical import ExtractionMethod, SourceType
from ..errors import Finding


@dataclass(frozen=True)
class SourceDocument:
    """Identity and metadata of a raw source document (tech design s3.1)."""

    source_id: str
    source_type: str = SourceType.RHP.value
    uri: Optional[str] = None
    content_hash: Optional[str] = None
    file_size_bytes: Optional[int] = None
    page_count: Optional[int] = None
    retrieval_timestamp: Optional[str] = None
    source_timestamp: Optional[str] = None

    def to_source_ref_dict(self) -> Dict[str, Any]:
        """Format as a `_sources` entry in canonical JSON."""
        out: Dict[str, Any] = {
            "source_id": self.source_id,
            "source_type": self.source_type,
        }
        if self.uri is not None:
            out["uri"] = self.uri
        if self.content_hash is not None:
            out["content_hash"] = self.content_hash
        if self.retrieval_timestamp is not None:
            out["retrieval_timestamp"] = self.retrieval_timestamp
        if self.source_timestamp is not None:
            out["source_timestamp"] = self.source_timestamp
        return out


@dataclass
class RawExtraction:
    """One candidate extracted field with provenance and confidence (tech design s3.2)."""

    field_path: str
    candidate_value: Any = None
    raw_text: Optional[str] = None
    raw_unit: Optional[str] = None
    page: Optional[int] = None
    locator: Optional[str] = None
    section: Optional[str] = None
    quote: Optional[str] = None
    extraction_method: str = ExtractionMethod.DETERMINISTIC_PDF.value
    extraction_confidence: float = 1.0
    is_unknown: bool = False
    notes: Optional[str] = None

    def to_evidence_dict(self, source_id: str) -> Dict[str, Any]:
        """Convert to an `_evidence` block entry in canonical JSON."""
        clean_path = self.field_path.replace(".", "-").replace("[", "_").replace("]", "")
        ev_id = f"EV-{clean_path}"
        out: Dict[str, Any] = {
            "evidence_id": ev_id,
            "source_id": source_id,
            "locator": self.locator or f"Page {self.page}" if self.page else "Document",
            "extraction_method": self.extraction_method,
            "extraction_confidence": round(self.extraction_confidence, 2),
        }
        if self.page is not None:
            out["page"] = self.page
        if self.section is not None:
            out["section"] = self.section
        if self.quote is not None:
            out["quote"] = self.quote
        elif self.raw_text is not None:
            out["quote"] = self.raw_text[:200]
        if self.notes is not None:
            out["note"] = self.notes
        return out


@dataclass
class ExtractionReport:
    """Summary and findings produced by the extraction layer."""

    source: SourceDocument
    extractions: List[RawExtraction] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def field_count(self) -> int:
        return len(self.extractions)

    @property
    def unknown_count(self) -> int:
        return sum(1 for e in self.extractions if e.is_unknown or e.candidate_value is None)

    @property
    def verified_count(self) -> int:
        return sum(1 for e in self.extractions if not e.is_unknown and e.candidate_value is not None)
