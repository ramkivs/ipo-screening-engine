"""Phase 5I: Comprehensive CLI integration test suite.

Covers all 23 requirements specified in Phase 5I gate:
1. CLI help
2. invalid command
3. missing required source
4. RHP extraction invocation
5. extract --enrich happy path
6. Price Band Notice integration
7. supplemental enrichment integration
8. external snapshot integration
9. preliminary mode
10. final mode
11. final mode missing price notice
12. stale external data
13. malformed external data
14. conflicting external sources
15. UNKNOWN preservation
16. genuine zero preservation
17. deterministic repeat execution
18. output artifact creation
19. error exit behavior
20. secret redaction
21. hardcoded-default regression
22. frozen-core integrity
23. golden evaluation
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

from conftest import ENGINE_ROOT, GOLDEN_DIR, REPO_ROOT

CLI = ENGINE_ROOT / "tools" / "ipo_screen.py"
PDF_SYNTHETIC = REPO_ROOT / "fixtures" / "filings" / "class_a_financial_lender.pdf"
VISHAL_INPUT = REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json"
PBN_CLEAN = REPO_ROOT / "fixtures" / "notices" / "clean_notice.txt"
CONNECTORS_DIR = REPO_ROOT / "fixtures" / "connectors"


def run_cli(*args: str, expect: int = 0) -> subprocess.CompletedProcess:
    completed = subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
    )
    assert completed.returncode == expect, (
        f"exit {completed.returncode} (wanted {expect})\n"
        f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
    )
    return completed


# --------------------------------------------------------------------------
# 1. CLI Help
# --------------------------------------------------------------------------


def test_cli_help():
    """Requirement 1: --help shows extract and assemble commands."""
    res = run_cli("--help")
    assert "extract" in res.stdout
    assert "assemble" in res.stdout
    assert "run" in res.stdout

    res_ext = run_cli("extract", "--help")
    assert "--enrich" in res_ext.stdout
    assert "--notice" in res_ext.stdout

    res_asm = run_cli("assemble", "--help")
    assert "--mode" in res_asm.stdout
    assert "--output" in res_asm.stdout


# --------------------------------------------------------------------------
# 2. Invalid Command
# --------------------------------------------------------------------------


def test_invalid_command():
    """Requirement 2: Unrecognized subcommand exits with usage error (2)."""
    run_cli("nonexistent-subcommand", expect=2)


# --------------------------------------------------------------------------
# 3. Missing Required Source
# --------------------------------------------------------------------------


def test_missing_required_source():
    """Requirement 3: Calling extract or assemble without positional argument exits with 2."""
    run_cli("extract", expect=2)
    run_cli("assemble", expect=2)


# --------------------------------------------------------------------------
# 4. RHP Extraction Invocation
# --------------------------------------------------------------------------


def test_rhp_extraction_invocation(tmp_path):
    """Requirement 4: extract produces extraction summary and valid canonical JSON."""
    out_file = tmp_path / "raw_extracted.json"
    res = run_cli("extract", str(PDF_SYNTHETIC), "--output", str(out_file))

    assert "extraction summary" in res.stdout
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert "company_name" in data
    assert "issue" in data


# --------------------------------------------------------------------------
# 5. Extract --enrich Happy Path
# --------------------------------------------------------------------------


def test_extract_enrich_happy_path(tmp_path):
    """Requirement 5: extract --enrich integrates PBN and outputs enriched canonical JSON."""
    out_file = tmp_path / "enriched.json"
    res = run_cli(
        "extract",
        str(PDF_SYNTHETIC),
        "--enrich",
        "--notice",
        str(PBN_CLEAN),
        "--output",
        str(out_file),
        "--mode",
        "final",
    )

    assert "extraction summary" in res.stdout
    assert "enrichment summary" in res.stdout
    assert out_file.exists()

    data = json.loads(out_file.read_text(encoding="utf-8"))
    issue = data["issue"]
    assert issue["price_band_high"] == 220.0
    assert issue["price_band_low"] == 208.0
    assert issue["lot_size"] == 68


# --------------------------------------------------------------------------
# 6. Price Band Notice Integration
# --------------------------------------------------------------------------


def test_price_band_notice_integration(tmp_path):
    """Requirement 6: assemble integrates Price Band Notice text and overrides [●]."""
    # Create raw base input with [●] pricing
    base_input = json.loads(VISHAL_INPUT.read_text(encoding="utf-8"))
    base_input["issue"]["price_band_high"] = None
    base_input["issue"]["price_band_low"] = None
    base_input["issue"]["lot_size"] = None
    raw_file = tmp_path / "base_raw.json"
    raw_file.write_text(json.dumps(base_input), encoding="utf-8")

    out_file = tmp_path / "assembled.json"
    pbn_text = """PRICE BAND NOTICE
INITIAL PUBLIC OFFERING OF VISHAL NIRMITI LIMITED
NOTICE TO INVESTORS
THE FLOOR PRICE AND THE CAP PRICE
The Floor Price is Rs. 240.00 and the Cap Price is Rs. 250.00 per Equity Share.
Bids can be made for a minimum of 60 Equity Shares.
BID OPENS ON: Tuesday, October 06, 2026
BID CLOSES ON: Thursday, October 08, 2026
"""
    pbn_file = tmp_path / "custom_pbn.txt"
    pbn_file.write_text(pbn_text, encoding="utf-8")

    res = run_cli(
        "assemble",
        str(raw_file),
        "--notice",
        str(pbn_file),
        "--output",
        str(out_file),
        "--mode",
        "final",
    )

    assert "assembly summary" in res.stdout
    assert "Rs. 240.0 - 250.0" in res.stdout
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["issue"]["price_band_high"] == 250.0
    assert data["issue"]["price_band_low"] == 240.0
    assert data["issue"]["lot_size"] == 60


# --------------------------------------------------------------------------
# 7. Supplemental Enrichment Integration
# --------------------------------------------------------------------------


def test_supplemental_enrichment_integration(tmp_path):
    """Requirement 7: assemble integrates Phase 5E supplemental contract JSON."""
    supp_data = {
        "contract_version": "1.0",
        "ipo_id": "VISHAL-NIRMITI-LIMITED",
        "analyst_assessment": {
            "moat_rating": {
                "raw_value": "wide",
                "normalized_value": "wide",
                "assessed_by": "Senior Analyst",
            }
        },
    }
    supp_file = tmp_path / "supp.json"
    supp_file.write_text(json.dumps(supp_data), encoding="utf-8")

    out_file = tmp_path / "assembled_supp.json"
    res = run_cli(
        "assemble",
        str(VISHAL_INPUT),
        "--supplemental",
        str(supp_file),
        "--output",
        str(out_file),
        "--mode",
        "final",
    )

    assert "assembly summary" in res.stdout
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["business"]["moat_rating"] == "wide"


# --------------------------------------------------------------------------
# 8. External Snapshot Integration
# --------------------------------------------------------------------------


def test_external_snapshot_integration(tmp_path):
    """Requirement 8: assemble integrates external market and peer snapshots."""
    market_file = CONNECTORS_DIR / "01_valid_subscription.json"
    peer_file = CONNECTORS_DIR / "04_valid_peer_snapshot.json"
    out_file = tmp_path / "assembled_ext.json"

    res = run_cli(
        "assemble",
        str(VISHAL_INPUT),
        "--market",
        str(market_file),
        "--peers",
        str(peer_file),
        "--output",
        str(out_file),
        "--mode",
        "final",
    )

    assert "assembly summary" in res.stdout
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["market"]["qib_subscription"] == 1.0
    assert len(data["peers"]) >= 2


# --------------------------------------------------------------------------
# 9. Preliminary Mode
# --------------------------------------------------------------------------


def test_preliminary_mode(tmp_path):
    """Requirement 9: preliminary mode succeeds even if price band notice is missing."""
    raw_input = json.loads(VISHAL_INPUT.read_text(encoding="utf-8"))
    raw_input["issue"]["price_band_high"] = None
    raw_input["issue"]["price_band_low"] = None
    raw_input["issue"]["lot_size"] = None
    raw_file = tmp_path / "raw_prelim.json"
    raw_file.write_text(json.dumps(raw_input), encoding="utf-8")

    out_file = tmp_path / "out_prelim.json"
    res = run_cli("assemble", str(raw_file), "--mode", "preliminary", "--output", str(out_file))

    assert "assembly summary" in res.stdout
    assert "mode             preliminary" in res.stdout
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["issue"]["price_band_high"] is None


# --------------------------------------------------------------------------
# 10. Final Mode
# --------------------------------------------------------------------------


def test_final_mode(tmp_path):
    """Requirement 10: final mode succeeds when pricing mechanics are complete."""
    out_file = tmp_path / "out_final.json"
    res = run_cli(
        "assemble",
        str(VISHAL_INPUT),
        "--notice",
        str(PBN_CLEAN),
        "--mode",
        "final",
        "--output",
        str(out_file),
    )
    assert "mode             final" in res.stdout
    assert out_file.exists()


# --------------------------------------------------------------------------
# 11. Final Mode Missing Price Notice Fails Closed
# --------------------------------------------------------------------------


def test_final_mode_missing_price_notice_fails_closed(tmp_path):
    """Requirement 11: final mode fails closed (exit 1) if price band is missing."""
    raw_input = json.loads(VISHAL_INPUT.read_text(encoding="utf-8"))
    raw_input["issue"]["price_band_high"] = None
    raw_input["issue"]["price_band_low"] = None
    raw_input["issue"]["lot_size"] = None
    raw_file = tmp_path / "missing_price.json"
    raw_file.write_text(json.dumps(raw_input), encoding="utf-8")

    res = run_cli("assemble", str(raw_file), "--mode", "final", expect=1)
    assert "Final evaluation mode requires verified Price Band Notice" in res.stderr


# --------------------------------------------------------------------------
# 12. Stale External Data
# --------------------------------------------------------------------------


def test_stale_external_data(tmp_path):
    """Requirement 12: Stale external data is handled without fabricating currency."""
    stale_file = CONNECTORS_DIR / "05_stale_snapshot.json"
    out_file = tmp_path / "stale_out.json"

    res = run_cli(
        "assemble",
        str(VISHAL_INPUT),
        "--market",
        str(stale_file),
        "--mode",
        "preliminary",
        "--output",
        str(out_file),
    )
    assert res.returncode == 0
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["market"]["qib_subscription"] == 0.45


# --------------------------------------------------------------------------
# 13. Malformed External Data
# --------------------------------------------------------------------------


def test_malformed_external_data(tmp_path):
    """Requirement 13: Corrupted JSON input fails closed with exit code 1."""
    corrupted_file = tmp_path / "corrupted.json"
    corrupted_file.write_text("{this is not valid json!}", encoding="utf-8")

    res = run_cli("assemble", str(corrupted_file), expect=1)
    assert "error:" in res.stderr


# --------------------------------------------------------------------------
# 14. Conflicting External Sources
# --------------------------------------------------------------------------


def test_conflicting_external_sources(tmp_path):
    """Requirement 14: Conflicting authoritative sources fail closed."""
    invalid_notice_file = REPO_ROOT / "fixtures" / "notices" / "invalid_collar_notice.txt"
    res = run_cli(
        "assemble",
        str(VISHAL_INPUT),
        "--notice",
        str(invalid_notice_file),
        "--mode",
        "final",
        expect=1,
    )
    assert "INVALID_COLLAR_SPREAD" in res.stderr or "SEBI ICDR 20% collar" in res.stderr


# --------------------------------------------------------------------------
# 15. UNKNOWN Preservation
# --------------------------------------------------------------------------


def test_unknown_preservation(tmp_path):
    """Requirement 15: Missing fields evaluate to null/None, never 0 or false."""
    raw_input = json.loads(VISHAL_INPUT.read_text(encoding="utf-8"))
    raw_input["issue"]["price_band_high"] = None
    raw_input["issue"]["price_band_low"] = None
    raw_input["issue"]["lot_size"] = None
    raw_input["issue"]["fresh_shares"] = None
    raw_file = tmp_path / "unknown_raw.json"
    raw_file.write_text(json.dumps(raw_input), encoding="utf-8")

    out_file = tmp_path / "unknown_out.json"
    run_cli("assemble", str(raw_file), "--mode", "preliminary", "--output", str(out_file))

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["issue"]["price_band_high"] is None
    assert data["issue"]["price_band_low"] is None
    assert data["issue"]["lot_size"] is None


# --------------------------------------------------------------------------
# 16. Genuine Zero Preservation
# --------------------------------------------------------------------------


def test_genuine_zero_preservation(tmp_path):
    """Requirement 16: Genuine 0 values are preserved as 0.0, not coerced to None."""
    zero_market = CONNECTORS_DIR / "12_zero_vs_unavailable.json"
    out_file = tmp_path / "zero_out.json"

    run_cli(
        "assemble",
        str(VISHAL_INPUT),
        "--market",
        str(zero_market),
        "--mode",
        "preliminary",
        "--output",
        str(out_file),
    )

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["market"]["qib_subscription"] == 0.0
    assert data["market"]["nii_subscription"] == 0.0


# --------------------------------------------------------------------------
# 17. Deterministic Repeat Execution
# --------------------------------------------------------------------------


def test_deterministic_repeat_execution(tmp_path):
    """Requirement 17: Repeated CLI invocations over identical inputs yield identical outputs."""
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    run_cli("assemble", str(VISHAL_INPUT), "--notice", str(PBN_CLEAN), "--output", str(out1))
    run_cli("assemble", str(VISHAL_INPUT), "--notice", str(PBN_CLEAN), "--output", str(out2))

    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# 18. Output Artifact Creation
# --------------------------------------------------------------------------


def test_output_artifact_creation(tmp_path):
    """Requirement 18: Output file path is created and contains valid JSON."""
    out_file = tmp_path / "nested" / "dir" / "out.json"
    res = run_cli("assemble", str(VISHAL_INPUT), "--output", str(out_file))

    assert out_file.exists()
    assert f"canonical json   {out_file}" in res.stdout


# --------------------------------------------------------------------------
# 19. Error Exit Behavior
# --------------------------------------------------------------------------


def test_error_exit_behavior():
    """Requirement 19: Actionable error message printed on failure with non-zero exit."""
    res = run_cli("assemble", "nonexistent_file_path.json", expect=1)
    assert "error:" in res.stderr
    assert "not found" in res.stderr


# --------------------------------------------------------------------------
# 20. Secret Redaction
# --------------------------------------------------------------------------


def test_secret_redaction(tmp_path):
    """Requirement 20: Secrets, API keys, and bearer tokens are never printed or saved."""
    secret_file = CONNECTORS_DIR / "secret_leak_payload.json"
    out_file = tmp_path / "sanitized_out.json"

    res = run_cli("assemble", str(VISHAL_INPUT), "--market", str(secret_file), "--output", str(out_file))

    # Output artifact is sanitized
    out_text = out_file.read_text(encoding="utf-8")
    assert "sec_live" not in out_text
    assert "sec_live" not in res.stdout
    assert "sec_live" not in res.stderr


# --------------------------------------------------------------------------
# 21. Hardcoded-Default Regression
# --------------------------------------------------------------------------


def test_hardcoded_default_regression(tmp_path):
    """Requirement 21: Proves 208, 220, 68, 9.46, 85.33 are not silently introduced."""
    # Synthetic extraction on class_a without template and without PBN
    out_file = tmp_path / "extracted_no_fallbacks.json"
    run_cli(
        "extract",
        str(PDF_SYNTHETIC),
        "--enrich",
        "--output",
        str(out_file),
        "--mode",
        "preliminary",
    )

    data = json.loads(out_file.read_text(encoding="utf-8"))
    issue = data.get("issue", {})
    biz = data.get("business", {})

    # None of the forbidden Vishal Nirmiti defaults appear
    assert issue.get("price_band_low") != 208
    assert issue.get("price_band_high") != 220
    assert issue.get("lot_size") != 68
    assert issue.get("post_issue_eps") != 9.46
    assert biz.get("top5_customer_pct") != 85.33


# --------------------------------------------------------------------------
# 22. Frozen-Core Integrity
# --------------------------------------------------------------------------


def test_frozen_core_integrity():
    """Requirement 22: Evaluation core remains frozen with zero modifications."""
    core_files = [
        REPO_ROOT / "engine" / "ipo_screening" / "derived.py",
        REPO_ROOT / "engine" / "ipo_screening" / "scoring.py",
        REPO_ROOT / "engine" / "ipo_screening" / "knockouts.py",
        REPO_ROOT / "engine" / "ipo_screening" / "snapshots.py",
        REPO_ROOT / "engine" / "ipo_screening" / "evaluation.py",
    ]
    for cf in core_files:
        assert cf.exists()
        # Verify git status has no changes for core files
        proc = subprocess.run(["git", "diff", "--", str(cf)], capture_output=True, text=True, cwd=str(REPO_ROOT))
        assert proc.stdout.strip() == "", f"Core file {cf.name} was modified!"


# --------------------------------------------------------------------------
# 23. Golden Evaluation Regression
# --------------------------------------------------------------------------


def test_golden_evaluation_regression():
    """Requirement 23: Assembled golden input produces exact frozen result hash."""
    res = run_cli(
        "assemble",
        str(VISHAL_INPUT),
        "--run",
        "--mode",
        "final",
        "--at",
        "2026-10-05T12:00:00Z",
    )

    expected_hash = "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
    assert expected_hash in res.stdout
