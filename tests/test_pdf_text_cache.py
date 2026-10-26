"""Isolation contracts for the opt-in text-only test optimization."""
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from pdf_text_cache import PDFTextCache


def page(data=b"filing", number=1):
    reader = SimpleNamespace(stream=BytesIO(data))
    return SimpleNamespace(indirect_reference=SimpleNamespace(pdf=reader, idnum=number, generation=0))


def test_only_text_is_reused_across_fresh_readers():
    cache = PDFTextCache()
    calls = []
    wrapped = cache.wrap(lambda p: calls.append(p) or "immutable text")
    a, b = page(), page()
    assert wrapped(a) == wrapped(b) == "immutable text"
    assert calls == [a]
    assert a.indirect_reference.pdf is not b.indirect_reference.pdf
    assert (cache.hits, cache.misses) == (1, 1)

    # Exercise the real pypdf reader/reference seam too, with a tiny fixture.
    from pypdf import PdfReader
    from pypdf._page import PageObject

    fixture = Path(__file__).parent.parent / "fixtures/filings/complete_sample_rhp.pdf"
    cache = PDFTextCache()
    wrapped = cache.wrap(PageObject.extract_text)
    first = PdfReader(fixture).pages[0]
    second = PdfReader(fixture).pages[0]
    expected = first.extract_text()
    assert expected
    assert wrapped(first) == wrapped(second) == expected
    assert (cache.hits, cache.misses) == (1, 1)


def test_changed_bytes_and_other_pages_cannot_hit():
    cache = PDFTextCache()
    calls = []
    wrapped = cache.wrap(lambda p: calls.append(p) or str(len(calls)))
    assert [wrapped(p) for p in (page(), page(b"changed"), page(number=2))] == ["1", "2", "3"]
    assert cache.hits == 0


def test_arguments_visitors_and_layout_mode_bypass_cache():
    cache = PDFTextCache()
    calls = []
    wrapped = cache.wrap(lambda p, *a, **kw: calls.append((a, kw)) or "text")
    p = page()
    wrapped(p)
    wrapped(p, extraction_mode="layout")
    wrapped(p, visitor_text=lambda *args: None)
    wrapped(p, 90)
    assert len(calls) == 4
    assert cache.hits == 0


def test_errors_are_not_cached():
    cache = PDFTextCache()
    def fail(p):
        raise ValueError("bad page")
    wrapped = cache.wrap(fail)
    for _ in range(2):
        with pytest.raises(ValueError, match="bad page"):
            wrapped(page())
    assert not cache.text


def test_non_reader_objects_bypass_cache():
    cache = PDFTextCache()
    wrapped = cache.wrap(lambda p: "synthetic")
    assert wrapped(object()) == "synthetic"
    assert not cache.text
