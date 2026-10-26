"""Keep the conservative real-file/workflow inventory complete as tests grow."""
import re
from pathlib import Path

from tier_inventory import INTEGRATION_MODULES

# These use synthetic inputs, not large filing decoding. Pass-9 stays fast.
SYNTHETIC_EXCEPTIONS = {
    "test_aggregator_issue_terms.py",
    "test_issue_terms_cli.py",
    "test_pdf_text_cache.py",  # tests the cache with tiny fake readers
    "test_suite_tiers.py",  # this inventory guard itself
}


def test_real_file_and_ingestion_modules_have_an_explicit_tier():
    root = Path(__file__).parent
    candidates = {
        p.name for p in root.glob("test*.py")
        if re.search(r"pdf|ingest", p.read_text(encoding="utf-8"), re.IGNORECASE)
    }
    assert candidates - SYNTHETIC_EXCEPTIONS <= INTEGRATION_MODULES
    assert all((root / name).is_file() for name in INTEGRATION_MODULES)
    assert not INTEGRATION_MODULES & SYNTHETIC_EXCEPTIONS
