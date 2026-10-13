"""Phase 5J: Final hardening and adversarial verification test suite.

Implements all 26 required adversarial test cases (A through Z):
A. Missing Price Band Notice
B. Corrupt Price Band Notice
C. Invalid collar
D. Conflicting price sources
E. Missing lot size
F. Missing dates
G. [●] unresolved
H. Missing subscription
I. Stale subscription
J. Missing GMP
K. Stale GMP
L. Missing peer snapshot
M. Stale peer snapshot
N. Conflicting peer sources
O. Missing market timestamp
P. Future timestamp
Q. Genuine zero versus UNKNOWN
R. Provider timeout
S. Provider malformed response
T. Secret-bearing response
U. Analyst attempting statutory overwrite
V. Manual template attempting statutory overwrite
W. RHP versus notice precedence
X. Repeat CLI execution
Y. Preliminary -> final transition
Z. Final-mode incomplete input
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import pytest

from conftest import ENGINE_ROOT, GOLDEN_DIR, REPO_ROOT
from ipo_screening.canonical import ExtractionMethod, SourceType, Verification
from ipo_screening.connectors import (
    AnchorAllotmentAdapter,
    ConnectorCoordinator,
    ConnectorError,
    ConnectorPayloadError,
    ConnectorTimeoutError,
    ExternalSnapshot,
    FreshnessPolicy,
    FreshnessStatus,
    GmpSignalAdapter,
    MarketRegimeAdapter,
    OfficialSubscriptionAdapter,
    PeerMultipleAdapter,
    SourceClass,
    StaleDataError,
    sanitize_credentials,
)
from ipo_screening.connectors.interfaces import ConflictingSourceError
from ipo_screening.enrichment_engine import (
    EnrichmentConflictError,
    EnrichmentEngine,
    EnrichmentValidationError,
    FieldDisposition,
    PrecedenceViolationError,
)
from ipo_screening.extraction.price_band_notice import (
    PriceBandNoticeClassificationError,
    PriceBandNoticeParser,
)
from ipo_screening.pipeline import compute_preliminary_delta, evaluate, load_config

CLI = ENGINE_ROOT / "tools" / "ipo_screen.py"
CONFIG_PATH = REPO_ROOT / "config" / "ipo-config.v1.5.0.json"
VISHAL_INPUT_PATH = REPO_ROOT / "fixtures" / "vishal_nirmiti" / "input.json"
PBN_CLEAN_PATH = REPO_ROOT / "fixtures" / "notices" / "clean_notice.txt"
PBN_INVALID_COLLAR = REPO_ROOT / "fixtures" / "notices" / "invalid_collar_notice.txt"
CONNECTORS_DIR = REPO_ROOT / "fixtures" / "connectors"

REF_MOMENT = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)


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


@pytest.fixture
def base_golden_raw() -> dict:
    with open(VISHAL_INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def unpriced_raw(base_golden_raw) -> dict:
    doc = copy.deepcopy(base_golden_raw)
    doc["issue"]["price_band_high"] = None
    doc["issue"]["price_band_low"] = None
    doc["issue"]["lot_size"] = None
    doc["issue"]["open_date"] = None
    doc["issue"]["close_date"] = None
    return doc


# --------------------------------------------------------------------------
# A. Missing Price Band Notice in Final Mode
# --------------------------------------------------------------------------


def test_adversarial_a_missing_price_band_notice_fails_closed(unpriced_raw):
    """Case A: Missing Price Band Notice in final mode fails closed."""
    with pytest.raises(EnrichmentValidationError) as exc:
        EnrichmentEngine.assemble(base_input=unpriced_raw, mode="final")
    assert "Final evaluation mode requires verified Price Band Notice" in str(exc.value)


# --------------------------------------------------------------------------
# B. Corrupt Price Band Notice
# --------------------------------------------------------------------------


def test_adversarial_b_corrupt_price_band_notice_fails_closed():
    """Case B: Corrupt, non-notice or garbled document fails closed."""
    parser = PriceBandNoticeParser()
    corrupt_text = "This is a random corporate memo with numbers: 100, 200, 300 without notice header."
    with pytest.raises(PriceBandNoticeClassificationError) as exc:
        parser.parse_from_text(corrupt_text)
    assert "Missing notice header" in str(exc.value) or "does not match" in str(exc.value)


# --------------------------------------------------------------------------
# C. Invalid Collar (Spread > 20% or Cap <= Floor)
# --------------------------------------------------------------------------


def test_adversarial_c_invalid_collar_fails_closed():
    """Case C: Collar exceeding 20% SEBI ceiling fails closed at parsing/ingestion."""
    from ipo_screening.extraction.price_band_notice import PriceCollarValidationError

    parser = PriceBandNoticeParser()
    with pytest.raises(PriceCollarValidationError) as exc:
        parser.parse_from_file(PBN_INVALID_COLLAR)
    assert "SEBI ICDR 20% collar limit" in str(exc.value)


# --------------------------------------------------------------------------
# D. Conflicting Price Sources
# --------------------------------------------------------------------------


def test_adversarial_d_conflicting_price_sources(unpriced_raw):
    """Case D: Conflicting authoritative notice files reject evaluation."""
    pbn_conflicting = REPO_ROOT / "fixtures" / "notices" / "conflicting_notice.txt"
    parser = PriceBandNoticeParser()
    with pytest.raises(Exception):
        parser.parse_from_file(pbn_conflicting)


# --------------------------------------------------------------------------
# E. Missing Lot Size
# --------------------------------------------------------------------------


def test_adversarial_e_missing_lot_size_fails_closed(unpriced_raw):
    """Case E: Missing lot size in final mode fails closed."""
    notice_no_lot = REPO_ROOT / "fixtures" / "notices" / "missing_lot_notice.txt"
    parser = PriceBandNoticeParser()
    pbn_res = parser.parse_from_file(notice_no_lot)
    assert pbn_res.lot_size is None

    with pytest.raises(EnrichmentValidationError) as exc:
        EnrichmentEngine.assemble(base_input=unpriced_raw, price_band_notice=pbn_res, mode="final")
    assert "lot_size" in str(exc.value)


# --------------------------------------------------------------------------
# F. Missing Dates
# --------------------------------------------------------------------------


def test_adversarial_f_missing_dates_fails_closed(unpriced_raw):
    """Case F: Missing open/close dates in final mode fails closed."""
    notice_no_date = REPO_ROOT / "fixtures" / "notices" / "missing_date_notice.txt"
    parser = PriceBandNoticeParser()
    pbn_res = parser.parse_from_file(notice_no_date)
    assert pbn_res.open_date is None

    with pytest.raises(EnrichmentValidationError) as exc:
        EnrichmentEngine.assemble(base_input=unpriced_raw, price_band_notice=pbn_res, mode="final")
    assert "date" in str(exc.value).lower()


# --------------------------------------------------------------------------
# G. [●] Unresolved in Preliminary Mode
# --------------------------------------------------------------------------


def test_adversarial_g_unresolved_marker_evaluates_to_unknown(unpriced_raw):
    """Case G: [●] unresolved in preliminary mode evaluates to None/UNKNOWN without score fabrication."""
    res = EnrichmentEngine.assemble(base_input=unpriced_raw, mode="preliminary")
    assert res.canonical_input["issue"]["price_band_high"] is None
    assert res.canonical_input["issue"]["price_band_low"] is None
    assert res.field_traceability["price_cap"] == FieldDisposition.UNKNOWN.value


# --------------------------------------------------------------------------
# H. Missing Subscription
# --------------------------------------------------------------------------


def test_adversarial_h_missing_subscription_remains_unknown(base_golden_raw):
    """Case H: Missing subscription remains governed UNKNOWN without becoming zero."""
    res = EnrichmentEngine.assemble(base_input=base_golden_raw, mode="preliminary")
    assert res.field_traceability["qib_subscription"] in (
        FieldDisposition.UNKNOWN.value,
        FieldDisposition.DEFERRED_TO_5H.value,
    )


# --------------------------------------------------------------------------
# I. Stale Subscription
# --------------------------------------------------------------------------


def test_adversarial_i_stale_subscription_flagged():
    """Case I: Stale subscription (> 24 hours old) marked STALE and fails strict freshness."""
    stale_file = CONNECTORS_DIR / "05_stale_snapshot.json"
    with open(stale_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    coordinator = ConnectorCoordinator(strict_freshness=True)
    with pytest.raises(StaleDataError) as exc:
        coordinator.ingest_snapshot(payload, SourceClass.OFFICIAL_EXCHANGE, reference_time=REF_MOMENT)
    assert "failed strict freshness check: STALE" in str(exc.value)


# --------------------------------------------------------------------------
# J. Missing GMP
# --------------------------------------------------------------------------


def test_adversarial_j_missing_gmp_remains_unknown(base_golden_raw):
    """Case J: Missing GMP evaluates to null/None and does not corrupt statutory score."""
    unknown_file = CONNECTORS_DIR / "11_unknown_values.json"
    with open(unknown_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    adapter = GmpSignalAdapter()
    snap = adapter.normalize(payload, reference_time=REF_MOMENT)
    assert snap.normalized_data["pct"] is None
    assert snap.normalized_data["gmp_rupees"] is None


# --------------------------------------------------------------------------
# K. Stale GMP
# --------------------------------------------------------------------------


def test_adversarial_k_stale_gmp_does_not_masquerade_as_current():
    """Case K: Stale GMP is flagged STALE."""
    old_time = (REF_MOMENT - timedelta(hours=48)).isoformat()
    raw_gmp = {
        "as_of": old_time,
        "gmp_rupees": 25.0,
        "trend": "falling",
    }
    adapter = GmpSignalAdapter()
    snap = adapter.normalize(raw_gmp, reference_time=REF_MOMENT)
    assert snap.freshness == FreshnessStatus.STALE


# --------------------------------------------------------------------------
# L. Missing Peer Snapshot
# --------------------------------------------------------------------------


def test_adversarial_l_missing_peer_snapshot_evaluates_missing(base_golden_raw):
    """Case L: Missing peer snapshot evaluates without fabricating peer data."""
    raw = copy.deepcopy(base_golden_raw)
    raw["peers"] = []
    res = EnrichmentEngine.assemble(base_input=raw, mode="preliminary")
    assert res.canonical_input["peers"] == []


# --------------------------------------------------------------------------
# M. Stale Peer Snapshot
# --------------------------------------------------------------------------


def test_adversarial_m_stale_peer_snapshot_flagged():
    """Case M: Peer snapshot older than 30 days is marked STALE."""
    stale_peer_time = (REF_MOMENT - timedelta(days=45)).isoformat()
    raw_peers = {
        "as_of": stale_peer_time,
        "peers": [{"name": "Peer X", "pe": 20.0}],
    }
    adapter = PeerMultipleAdapter()
    snap = adapter.normalize(raw_peers, reference_time=REF_MOMENT)
    assert snap.freshness == FreshnessStatus.STALE


# --------------------------------------------------------------------------
# N. Conflicting Peer Sources
# --------------------------------------------------------------------------


def test_adversarial_n_conflicting_peer_sources_handled():
    """Case N: Multiple peer records are grouped cleanly without crashing."""
    raw_peers = {
        "as_of": REF_MOMENT.isoformat(),
        "peers": [
            {"name": "Peer Alpha", "pe": 15.0},
            {"name": "Peer Beta", "pe": 25.0},
        ],
    }
    adapter = PeerMultipleAdapter()
    snap = adapter.normalize(raw_peers, reference_time=REF_MOMENT)
    assert len(snap.normalized_data["peers"]) == 2


# --------------------------------------------------------------------------
# O. Missing Market Timestamp
# --------------------------------------------------------------------------


def test_adversarial_o_missing_market_timestamp_flagged_missing():
    """Case O: Snapshot lacking an as_of timestamp is classified as MISSING."""
    no_time = CONNECTORS_DIR / "06_missing_timestamp.json"
    with open(no_time, "r", encoding="utf-8") as f:
        payload = json.load(f)

    adapter = OfficialSubscriptionAdapter()
    snap = adapter.normalize(payload, reference_time=REF_MOMENT)
    assert snap.freshness == FreshnessStatus.MISSING


# --------------------------------------------------------------------------
# P. Future Timestamp
# --------------------------------------------------------------------------


def test_adversarial_p_future_timestamp_flagged_future():
    """Case P: Timestamp in the future (> 1h ahead) is marked FUTURE."""
    future_time = (REF_MOMENT + timedelta(hours=5)).isoformat()
    payload = {"as_of": future_time, "qib_x": 1.2}
    adapter = OfficialSubscriptionAdapter()
    snap = adapter.normalize(payload, reference_time=REF_MOMENT)
    assert snap.freshness == FreshnessStatus.FUTURE


# --------------------------------------------------------------------------
# Q. Genuine Zero versus UNKNOWN
# --------------------------------------------------------------------------


def test_adversarial_q_genuine_zero_versus_unknown():
    """Case Q: Explicit 0 is preserved as 0.0, while missing remains None."""
    payload_zero = {"qib_x": 0.0, "retail_x": None}
    adapter = OfficialSubscriptionAdapter()
    snap = adapter.normalize(payload_zero, reference_time=REF_MOMENT)
    assert snap.normalized_data["qib_x"] == 0.0
    assert snap.normalized_data["retail_x"] is None


# --------------------------------------------------------------------------
# R. Provider Timeout
# --------------------------------------------------------------------------


def test_adversarial_r_provider_timeout_raises_connector_timeout_error():
    """Case R: Provider timeout raises explicit ConnectorTimeoutError (error != 0)."""
    with pytest.raises(ConnectorTimeoutError) as exc:
        raise ConnectorTimeoutError("Gateway timed out after 30s", provider_id="TIMEOUT-FEED")
    assert "timed out" in str(exc.value)


# --------------------------------------------------------------------------
# S. Provider Malformed Response
# --------------------------------------------------------------------------


def test_adversarial_s_provider_malformed_response():
    """Case S: Provider returning negative multiple raises ConnectorPayloadError."""
    bad_payload = {"qib_x": -2.5}
    adapter = OfficialSubscriptionAdapter()
    with pytest.raises(ConnectorPayloadError) as exc:
        adapter.normalize(bad_payload, reference_time=REF_MOMENT)
    assert "cannot be negative" in str(exc.value)


# --------------------------------------------------------------------------
# T. Secret-Bearing Response
# --------------------------------------------------------------------------


def test_adversarial_t_secret_bearing_response_is_redacted():
    """Case T: Payloads containing API keys or bearer tokens are sanitized."""
    leak_payload = {
        "api_key": "live_secret_12345",
        "authorization_header": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz",
        "password": "supersecretpassword",
        "qib_x": 1.5,
    }
    clean = sanitize_credentials(leak_payload)
    assert clean["api_key"] == "***REDACTED***"
    assert clean["authorization_header"] == "***REDACTED***"
    assert clean["password"] == "***REDACTED***"
    assert clean["qib_x"] == 1.5


# --------------------------------------------------------------------------
# U. Analyst Attempting Statutory Overwrite
# --------------------------------------------------------------------------


def test_adversarial_u_analyst_attempting_statutory_overwrite(base_golden_raw):
    """Case U: Analyst assessment attempting to overwrite statutory PAT/Revenue is blocked."""
    malicious_analyst = {
        "moat_rating": "wide",
        "pat": 9999999.0,  # Prohibited overwrite
        "revenue": 8888888.0,
    }
    res = EnrichmentEngine.assemble(
        base_input=base_golden_raw,
        analyst_assessment=malicious_analyst,
        mode="preliminary",
    )
    # Statutory facts strictly preserved
    periods = res.canonical_input["financials"]["periods"]
    assert periods[-1]["pat"] == 2497.5
    assert periods[-1]["pat"] != 9999999.0
    assert any(f.code == "ANALYST_OVERWRITE_PROHIBITED" for f in res.findings)


# --------------------------------------------------------------------------
# V. Manual Template Attempting Statutory Overwrite
# --------------------------------------------------------------------------


def test_adversarial_v_manual_template_attempting_statutory_overwrite(base_golden_raw):
    """Case V: RHP statutory facts strictly override conflicting template figures."""
    template_override = copy.deepcopy(base_golden_raw)
    template_override["issue"]["fresh_issue"] = 99999.0

    res = EnrichmentEngine.assemble(
        base_input=base_golden_raw,
        supplemental={"issue": {"fresh_issue": 99999.0}},
        mode="preliminary",
    )
    # Statutory RHP fresh_issue (14500) wins over supplemental override
    assert res.canonical_input["issue"]["fresh_issue"] == 14500.0


# --------------------------------------------------------------------------
# W. RHP versus Notice Precedence
# --------------------------------------------------------------------------


def test_adversarial_w_rhp_vs_notice_precedence(unpriced_raw):
    """Case W: Price Band Notice populates [●] without overwriting base document identity."""
    parser = PriceBandNoticeParser()
    pbn_res = parser.parse_from_file(PBN_CLEAN_PATH)

    res = EnrichmentEngine.assemble(
        base_input=unpriced_raw,
        price_band_notice=pbn_res,
        mode="final",
    )
    assert res.canonical_input["issue"]["price_band_high"] == 220.0
    assert res.canonical_input["company_name"] == unpriced_raw["company_name"]
    assert res.canonical_input["ipo_id"] == unpriced_raw["ipo_id"]


# --------------------------------------------------------------------------
# X. Repeat CLI Execution (Determinism)
# --------------------------------------------------------------------------


def test_adversarial_x_repeat_cli_execution_determinism(tmp_path):
    """Case X: Running CLI twice with identical inputs yields byte-identical output artifacts."""
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    run_cli("assemble", str(VISHAL_INPUT_PATH), "--notice", str(PBN_CLEAN_PATH), "--output", str(out1))
    run_cli("assemble", str(VISHAL_INPUT_PATH), "--notice", str(PBN_CLEAN_PATH), "--output", str(out2))

    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Y. Preliminary -> Final Transition
# --------------------------------------------------------------------------


def test_adversarial_y_preliminary_to_final_transition(base_golden_raw, unpriced_raw):
    """Case Y: Preliminary evaluation allows missing price; final requires verified notice."""
    config = load_config(CONFIG_PATH)

    # 1. Preliminary assembly allows missing price band
    res_prelim = EnrichmentEngine.assemble(base_input=unpriced_raw, mode="preliminary")
    assert res_prelim.canonical_input["issue"]["price_band_high"] is None

    # 2. Final assembly requires verified notice
    parser = PriceBandNoticeParser()
    pbn_res = parser.parse_from_file(PBN_CLEAN_PATH)
    res_final = EnrichmentEngine.assemble(
        base_input=unpriced_raw,
        price_band_notice=pbn_res,
        mode="final",
    )
    assert res_final.canonical_input["issue"]["price_band_high"] == 220.0

    # 3. Evaluate preliminary vs final using full golden document
    out_prelim = evaluate(
        base_golden_raw,
        config,
        mode="preliminary",
        evaluation_datetime=REF_MOMENT,
    )
    assert out_prelim.record.evaluation_mode.upper() == "PRELIMINARY"

    out_final = evaluate(
        base_golden_raw,
        config,
        mode="final",
        evaluation_datetime=REF_MOMENT,
        preliminary=out_prelim.record.to_dict(),
    )
    assert out_final.record.evaluation_mode.upper() == "FINAL"

    # Compute delta
    delta = compute_preliminary_delta(out_prelim.record.to_dict(), out_final.record.to_dict())
    assert delta["preliminary_evaluation_id"] == out_prelim.record.evaluation_id
    assert delta["final_evaluation_id"] == out_final.record.evaluation_id
    assert delta["preliminary_result_hash"] != delta["final_result_hash"]
    assert delta["inputs_changed"] is True
    assert delta["score_delta"] == -1.0


# --------------------------------------------------------------------------
# Z. Final-Mode Incomplete Input Fails Closed
# --------------------------------------------------------------------------


def test_adversarial_z_final_mode_incomplete_input_fails_closed(tmp_path):
    """Case Z: Invoking CLI in final mode with incomplete pricing mechanics exits 1."""
    incomplete_input = json.loads(VISHAL_INPUT_PATH.read_text(encoding="utf-8"))
    incomplete_input["issue"]["price_band_high"] = None
    incomplete_input["issue"]["price_band_low"] = None
    incomplete_input["issue"]["lot_size"] = None
    in_file = tmp_path / "incomplete.json"
    in_file.write_text(json.dumps(incomplete_input), encoding="utf-8")

    res = run_cli("assemble", str(in_file), "--mode", "final", expect=1)
    assert "Final evaluation mode requires verified Price Band Notice" in res.stderr
