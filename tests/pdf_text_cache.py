"""Opt-in test-only reuse of immutable pypdf page text.

Only audited modules enable this fixture. Never use it for tests mutating PDF
pages/readers or testing pypdf itself. No readers, canonical inputs, extraction
reports, services or stores are shared. The cache lives only in this pytest
process; there are no disk artifacts or stale cross-run results.
"""
from __future__ import annotations

import hashlib
from functools import wraps


class PDFTextCache:
    def __init__(self):
        self.text = {}
        self.hits = 0
        self.misses = 0

    def wrap(self, original):
        @wraps(original)
        def extract(page, *args, **kwargs):
            # Non-default extraction modes and visitors must execute normally.
            if args or kwargs:
                return original(page, *args, **kwargs)
            ref = getattr(page, "indirect_reference", None)
            reader = getattr(ref, "pdf", None)
            stream = getattr(reader, "stream", None)
            if not hasattr(stream, "getvalue"):
                return original(page)
            # Each fresh reader gets its own identity, computed from actual bytes,
            # never filename/path/mtime. Uploads and changed files cannot collide.
            digest = getattr(reader, "_test_pdf_text_digest", None)
            if digest is None:
                digest = hashlib.sha256(stream.getvalue()).hexdigest()
                reader._test_pdf_text_digest = digest
            key = (digest, ref.idnum, ref.generation)
            if key in self.text:
                self.hits += 1
                return self.text[key]
            result = original(page)  # exceptions are never cached
            if isinstance(result, str):
                self.text[key] = result
                self.misses += 1
            return result
        return extract
