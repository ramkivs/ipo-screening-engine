"""Re-evaluate the committed Jio RHP with the CURRENT engine.

Read-only diagnostic: it runs the real ingestion -> evaluation boundary on the
committed PDF and writes the response plus the evaluation record.  It writes no
engine store and changes no scoring rule.

The published record ``JIO-PLATFORMS-LIMITED-20261023-085751Z-final-29d9a601``
(34.0, 24-77, INSUFFICIENT_DATA) was produced by a tree whose 66 engine files
are fingerprinted in its ``runtime.json``; 20 of those 66 files differ from
``main``/``69a9ff9``.  This probe measures what the current engine returns.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "tests"))

from ipo_screening.issue_terms import IssueTermsResolver  # noqa: E402
from ipo_screening.presentation.service import PresentationConfig, PresentationService  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent
PDF = ROOT / "evidence" / "non-authoritative" / "jio" / "U72900GJ2019PLC110816_JIO.pdf"

MANUAL_TERMS = {
    "price_band_low": 1065.0,
    "price_band_high": 1119.0,
    "lot_size": 12,
    "ofs": 0.0,
    "fresh_issue": 302130.0,
}


def main() -> int:
    service = PresentationService(
        PresentationConfig(
            store_root=OUT / "evaluations",
            config_dir=ROOT / "config",
            issue_terms_resolver=IssueTermsResolver(providers=[]),
        )
    )
    result = service.ingest_document(
        file_bytes=PDF.read_bytes(),
        filename=PDF.name,
        mode="final",
        manual_terms=MANUAL_TERMS,
        manual_explanation="Current-engine probe (no official discovery provider available).",
        confirm_conflicts=True,
    )
    payload = result.model_dump() if hasattr(result, "model_dump") else vars(result)
    (OUT / "response.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    evaluation_id = payload.get("evaluation_id")
    record = OUT / "evaluations" / f"{evaluation_id}.json"
    if not record.exists():
        for candidate in sorted((OUT / "evaluations").glob("*.json")):
            record = candidate
            break
    print("evaluation_id", evaluation_id)
    print("record", record)
    print("final_score", payload.get("final_score"), "verdict", payload.get("verdict"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
