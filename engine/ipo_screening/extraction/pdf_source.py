"""PDF Source Adapter: document identity, SHA-256 computation and validation.

Technical Design v1.5 s3.1:
  Every source receives source ID, retrieval timestamp, source timestamp,
  content hash, source type, and URI/file reference.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import pypdf

from ..canonical import SourceType
from .interfaces import SourceDocument


class PDFSourceError(Exception):
    """Failure loading or reading a PDF source file."""


def compute_file_sha256(path: Path) -> str:
    """Compute the SHA-256 checksum of raw file bytes."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_pdf_source(
    file_path: str | Path,
    *,
    source_id: Optional[str] = None,
    source_type: str = SourceType.RHP.value,
) -> Tuple[SourceDocument, pypdf.PdfReader]:
    """Open and validate an RHP/DRHP PDF document.

    Raises :exc:`PDFSourceError` on non-existent, zero-byte, corrupted or
    unreadable encrypted files.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        raise PDFSourceError(f"PDF file does not exist: {path}")
    if not path.is_file():
        raise PDFSourceError(f"Path is not a regular file: {path}")

    file_size = path.stat().st_size
    if file_size == 0:
        raise PDFSourceError(f"PDF file is zero bytes (empty): {path}")

    content_hash = compute_file_sha256(path)

    try:
        reader = pypdf.PdfReader(str(path))
    except Exception as exc:
        raise PDFSourceError(f"Corrupted or invalid PDF format: {path} ({exc})") from exc

    if reader.is_encrypted:
        try:
            # Try decrypting with empty password if standard security handler
            success = reader.decrypt("")
            if not success:
                raise PDFSourceError(f"PDF is encrypted and password-protected: {path}")
        except Exception as exc:
            raise PDFSourceError(f"Cannot decrypt password-protected PDF: {path}") from exc

    page_count = len(reader.pages)
    if page_count == 0:
        raise PDFSourceError(f"PDF has 0 pages: {path}")

    doc_id = source_id or f"RHP-{path.stem.upper()[:24]}-{content_hash[:8]}"
    doc = SourceDocument(
        source_id=doc_id,
        source_type=source_type,
        uri=str(path),
        content_hash=content_hash,
        file_size_bytes=file_size,
        page_count=page_count,
        retrieval_timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    return doc, reader
