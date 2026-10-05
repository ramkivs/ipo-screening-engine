"""Excel historical projection.

Spec v1.5 s22 and s3.6: the Excel workbook is the human-analysis surface and
must be **generated from** the immutable evaluation records. It is not the
authoritative store.

Sheets produced (spec s22 list):

 1.  IPO_Master              10. Peer_Snapshots
 2.  Evaluations             11. Post_Listing
 3.  Module_Scores           12. Backtest
 4.  Criteria_Detail         13. Config_Versions
 5.  Knockouts               14. Run_Log
 6.  Penalties
 7.  Missing_Unverified
 8.  Evidence
 9.  Market_Snapshots

Historical rule: never replace historical rows. The projector is a pure
function of the stored records, so regenerating the workbook from the same
store reproduces the same workbook, and a new evaluation only ever appends
rows. Every row carries ``evaluation_id`` and ``result_hash`` so a line in the
workbook can be traced back to the immutable record it came from (tech design
s14).

The workbook is written deterministically: workbook properties are pinned and
sheet order, header order and row order are all derived from sorted keys, so
two projections of the same store produce byte-identical output.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from .evaluation import EvaluationStore
from .hashing import sha256_of
from .version import ENGINE_VERSION, SPEC_VERSION

#: Pinned so that two projections of the same store are byte-identical.
FIXED_TIMESTAMP = datetime(1980, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

SHEET_ORDER: Tuple[str, ...] = (
    "IPO_Master",
    "Evaluations",
    "Module_Scores",
    "Criteria_Detail",
    "Knockouts",
    "Penalties",
    "Missing_Unverified",
    "Evidence",
    "Market_Snapshots",
    "Peer_Snapshots",
    "Post_Listing",
    "Backtest",
    "Config_Versions",
    "Run_Log",
)

_HEADER_FILL = PatternFill("solid", fgColor="1F3864")
_HEADER_FONT = Font(bold=True, color="FFFFFF")
_EVIDENCE_FILL = PatternFill("solid", fgColor="FFF2CC")


def _flatten(prefix: str, value: Any, out: Dict[str, Any]) -> None:
    if isinstance(value, Mapping):
        for key in value:
            _flatten(f"{prefix}.{key}" if prefix else str(key), value[key], out)
    elif isinstance(value, (list, tuple)):
        out[prefix] = "; ".join(str(v) for v in value)
    else:
        out[prefix] = value


def _write_sheet(
    worksheet: Worksheet,
    headers: Sequence[str],
    rows: Iterable[Sequence[Any]],
    *,
    freeze: str = "A2",
) -> None:
    worksheet.append(list(headers))
    for cell in worksheet[1]:
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(vertical="center")
    for row in rows:
        worksheet.append(list(row))
    worksheet.freeze_panes = freeze
    if headers:
        worksheet.auto_filter.ref = (
            f"A1:{get_column_letter(len(headers))}{max(1, worksheet.max_row)}"
        )
    for index, header in enumerate(headers, start=1):
        width = max(12, min(56, len(str(header)) + 4))
        worksheet.column_dimensions[get_column_letter(index)].width = width


def _sort_records(records: Sequence[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    return sorted(
        records,
        key=lambda r: (
            str(r.get("ipo_id", "")),
            str(r.get("evaluation_timestamp", "")),
            str(r.get("evaluation_mode", "")),
            str(r.get("evaluation_id", "")),
        ),
    )


# --------------------------------------------------------------------------
# Row builders - one per sheet
# --------------------------------------------------------------------------


def _rows_ipo_master(records: Sequence[Mapping[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "ipo_id",
        "company_name",
        "board",
        "icdr_route",
        "sector_profile",
        "first_evaluation_id",
        "latest_evaluation_id",
        "evaluation_count",
        "latest_mode",
        "latest_score",
        "latest_verdict",
        "latest_confidence",
        "latest_knockout_status",
        "latest_result_hash",
    ]
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for record in _sort_records(records):
        grouped.setdefault(str(record.get("ipo_id")), []).append(record)
    rows: List[List[Any]] = []
    for ipo_id in sorted(grouped):
        entries = grouped[ipo_id]
        first, latest = entries[0], entries[-1]
        snapshot = latest.get("input_snapshot", {})
        rows.append(
            [
                ipo_id,
                latest.get("company_name"),
                snapshot.get("board"),
                snapshot.get("icdr_route"),
                snapshot.get("sector_profile"),
                first.get("evaluation_id"),
                latest.get("evaluation_id"),
                len(entries),
                latest.get("evaluation_mode"),
                (latest.get("score") or {}).get("final_score"),
                (latest.get("verdict") or {}).get("verdict"),
                (latest.get("confidence") or {}).get("level"),
                (latest.get("knockouts") or {}).get("status"),
                latest.get("result_hash"),
            ]
        )
    return headers, rows


def _rows_evaluations(records: Sequence[Mapping[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "company_name",
        "mode",
        "evaluation_timestamp",
        "score",
        "base_score",
        "lower_bound",
        "upper_bound",
        "confidence",
        "completeness_pct",
        "verdict",
        "verdict_band_score",
        "verdict_uncertain",
        "insufficient_data",
        "knockout_status",
        "penalties_total",
        "available_points",
        "total_evaluable_points",
        "unknown_points",
        "engine_version",
        "spec_version",
        "config_version",
        "config_hash",
        "input_hash",
        "source_manifest_hash",
        "market_snapshot_hash",
        "peer_snapshot_hash",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        score = record.get("score") or {}
        score_range = record.get("score_range") or {}
        verdict = record.get("verdict") or {}
        rows.append(
            [
                record.get("evaluation_id"),
                record.get("ipo_id"),
                record.get("company_name"),
                record.get("evaluation_mode"),
                record.get("evaluation_timestamp"),
                score.get("final_score"),
                score_range.get("base_score"),
                score_range.get("lower_bound"),
                score_range.get("upper_bound"),
                (record.get("confidence") or {}).get("level"),
                score.get("completeness_pct"),
                verdict.get("verdict"),
                verdict.get("band_score"),
                verdict.get("uncertain"),
                verdict.get("insufficient_data"),
                (record.get("knockouts") or {}).get("status"),
                score.get("penalties_total"),
                score_range.get("available_points"),
                score_range.get("total_evaluable_points"),
                score_range.get("unknown_points"),
                record.get("engine_version"),
                record.get("spec_version"),
                record.get("config_version"),
                record.get("config_hash"),
                record.get("input_snapshot_hash"),
                record.get("source_manifest_hash"),
                record.get("market_snapshot_hash"),
                record.get("peer_snapshot_hash"),
                record.get("result_hash"),
            ]
        )
    return headers, rows


def _rows_module_scores(records: Sequence[Mapping[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "mode",
        "module_id",
        "module_name",
        "score",
        "max",
        "available_points",
        "unknown_points",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        for module in (record.get("score") or {}).get("modules", []):
            rows.append(
                [
                    record.get("evaluation_id"),
                    record.get("ipo_id"),
                    record.get("evaluation_mode"),
                    module.get("module_id"),
                    module.get("name"),
                    module.get("score"),
                    module.get("max"),
                    module.get("available_points"),
                    module.get("unknown_points"),
                    record.get("result_hash"),
                ]
            )
    return headers, rows


def _rows_criteria_detail(records: Sequence[Mapping[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "mode",
        "module_id",
        "criterion_id",
        "label",
        "metric",
        "kind",
        "state",
        "value",
        "band",
        "score",
        "max",
        "min",
        "reason",
        "formula",
        "evidence_refs",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        for module in (record.get("score") or {}).get("modules", []):
            for criterion in module.get("criteria", []):
                rows.append(
                    [
                        record.get("evaluation_id"),
                        record.get("ipo_id"),
                        record.get("evaluation_mode"),
                        module.get("module_id"),
                        criterion.get("criterion_id"),
                        criterion.get("label"),
                        criterion.get("metric"),
                        criterion.get("kind"),
                        criterion.get("state"),
                        criterion.get("value"),
                        criterion.get("band"),
                        criterion.get("score"),
                        criterion.get("max"),
                        criterion.get("min"),
                        criterion.get("reason"),
                        criterion.get("formula"),
                        "; ".join(criterion.get("evidence_refs", [])),
                        record.get("result_hash"),
                    ]
                )
    return headers, rows


def _rows_knockouts(records: Sequence[Mapping[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "mode",
        "rule_id",
        "label",
        "state",
        "missing_inputs",
        "explanation",
        "required_inputs",
        "evidence",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        knockouts = record.get("knockouts") or {}
        for result in knockouts.get("results", []):
            evidence = "; ".join(
                f"{leaf.get('reference')}={leaf.get('truth')}"
                for leaf in result.get("leaves", [])
            )
            rows.append(
                [
                    record.get("evaluation_id"),
                    record.get("ipo_id"),
                    record.get("evaluation_mode"),
                    result.get("rule_id"),
                    result.get("label"),
                    result.get("state"),
                    "; ".join(result.get("missing", [])),
                    result.get("explanation"),
                    "; ".join(result.get("required", [])),
                    evidence,
                    record.get("result_hash"),
                ]
            )
    return headers, rows


def _rows_penalties(records: Sequence[Mapping[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "mode",
        "penalty_id",
        "label",
        "points",
        "state",
        "reason",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        for penalty in record.get("penalties", []):
            rows.append(
                [
                    record.get("evaluation_id"),
                    record.get("ipo_id"),
                    record.get("evaluation_mode"),
                    penalty.get("id"),
                    penalty.get("label"),
                    penalty.get("points"),
                    penalty.get("state"),
                    penalty.get("reason"),
                    record.get("result_hash"),
                ]
            )
    return headers, rows


def _rows_missing_unverified(
    records: Sequence[Mapping[str, Any]]
) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "mode",
        "category",
        "item",
        "detail",
        "points_affected",
        "state",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        for entry in record.get("missing_unverified", []):
            rows.append(
                [
                    record.get("evaluation_id"),
                    record.get("ipo_id"),
                    record.get("evaluation_mode"),
                    entry.get("category"),
                    entry.get("item"),
                    entry.get("detail"),
                    entry.get("points_affected"),
                    entry.get("state"),
                    record.get("result_hash"),
                ]
            )
    return headers, rows


def _rows_evidence(records: Sequence[Mapping[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "source_id",
        "source_type",
        "source_uri",
        "content_hash",
        "evidence_id",
        "locator",
        "page",
        "section",
        "quote",
        "extraction_method",
        "as_of",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        evidence = record.get("evidence") or {}
        sources = {s.get("source_id"): s for s in evidence.get("sources", [])}
        for item in evidence.get("evidence", []):
            source = sources.get(item.get("source_id"), {})
            rows.append(
                [
                    record.get("evaluation_id"),
                    record.get("ipo_id"),
                    item.get("source_id"),
                    source.get("source_type"),
                    source.get("uri"),
                    source.get("content_hash"),
                    item.get("evidence_id"),
                    item.get("locator"),
                    item.get("page"),
                    item.get("section"),
                    item.get("quoted_text"),
                    item.get("extraction_method"),
                    item.get("as_of"),
                    record.get("result_hash"),
                ]
            )
    return headers, rows


def _rows_market_snapshots(
    records: Sequence[Mapping[str, Any]]
) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "mode",
        "snapshot_id",
        "block",
        "status",
        "as_of",
        "age_hours",
        "values",
        "reason",
        "snapshot_hash",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        snapshot = record.get("market_snapshot") or {}
        for block in snapshot.get("blocks", []):
            values = block.get("values") or {}
            rows.append(
                [
                    record.get("evaluation_id"),
                    record.get("ipo_id"),
                    record.get("evaluation_mode"),
                    snapshot.get("snapshot_id"),
                    block.get("block"),
                    block.get("status"),
                    block.get("as_of"),
                    block.get("age_hours"),
                    "; ".join(f"{k}={v}" for k, v in sorted(values.items())),
                    block.get("reason"),
                    record.get("market_snapshot_hash"),
                    record.get("result_hash"),
                ]
            )
    return headers, rows


def _rows_peer_snapshots(
    records: Sequence[Mapping[str, Any]]
) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "mode",
        "snapshot_id",
        "peer_id",
        "peer_name",
        "status",
        "as_of",
        "age_days",
        "listed_years",
        "pe",
        "ev_ebitda",
        "pb",
        "ps",
        "roe_pct",
        "roa_pct",
        "reason",
        "snapshot_hash",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        snapshot = record.get("peer_snapshot") or {}
        for peer in snapshot.get("observations", []):
            rows.append(
                [
                    record.get("evaluation_id"),
                    record.get("ipo_id"),
                    record.get("evaluation_mode"),
                    snapshot.get("snapshot_id"),
                    peer.get("peer_id"),
                    peer.get("name"),
                    peer.get("status"),
                    peer.get("as_of"),
                    peer.get("age_days"),
                    peer.get("listed_years"),
                    peer.get("pe"),
                    peer.get("ev_ebitda"),
                    peer.get("pb"),
                    peer.get("ps"),
                    peer.get("roe_pct"),
                    peer.get("roa_pct"),
                    peer.get("reason"),
                    record.get("peer_snapshot_hash"),
                    record.get("result_hash"),
                ]
            )
    return headers, rows


def _rows_post_listing(
    records: Sequence[Mapping[str, Any]]
) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "mode",
        "listing_date",
        "listing_gain_pct",
        "return_1w_pct",
        "return_1m_pct",
        "return_6m_pct",
        "nifty_return_1m_pct",
        "nifty_return_6m_pct",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        snapshot = (record.get("input_snapshot") or {}).get("input", {}) or {}
        post = snapshot.get("post_listing") or {}
        if not post:
            continue
        rows.append(
            [
                record.get("evaluation_id"),
                record.get("ipo_id"),
                record.get("evaluation_mode"),
                post.get("listing_date"),
                post.get("listing_gain_pct"),
                post.get("return_1w_pct"),
                post.get("return_1m_pct"),
                post.get("return_6m_pct"),
                post.get("nifty_return_1m_pct"),
                post.get("nifty_return_6m_pct"),
                record.get("result_hash"),
            ]
        )
    return headers, rows


def _rows_backtest(records: Sequence[Mapping[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    """Score against realised outcome (spec s2 post-listing, s22 Backtest)."""
    headers = [
        "ipo_id",
        "evaluation_id",
        "mode",
        "evaluation_timestamp",
        "score",
        "verdict",
        "knockout_status",
        "listing_gain_pct",
        "return_1m_pct",
        "return_6m_pct",
        "outcome_6m_vs_nifty_pct",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        snapshot = (record.get("input_snapshot") or {}).get("input", {}) or {}
        post = snapshot.get("post_listing") or {}
        if not post:
            continue
        six_month = post.get("return_6m_pct")
        nifty = post.get("nifty_return_6m_pct")
        excess = None if six_month is None or nifty is None else round(six_month - nifty, 6)
        rows.append(
            [
                record.get("ipo_id"),
                record.get("evaluation_id"),
                record.get("evaluation_mode"),
                record.get("evaluation_timestamp"),
                (record.get("score") or {}).get("final_score"),
                (record.get("verdict") or {}).get("verdict"),
                (record.get("knockouts") or {}).get("status"),
                post.get("listing_gain_pct"),
                post.get("return_1m_pct"),
                six_month,
                excess,
                record.get("result_hash"),
            ]
        )
    return headers, rows


def _rows_config_versions(
    records: Sequence[Mapping[str, Any]]
) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "config_version",
        "config_hash",
        "spec_version",
        "first_seen_timestamp",
        "evaluation_count",
        "ipos",
    ]
    grouped: Dict[Tuple[str, str], List[Mapping[str, Any]]] = {}
    for record in _sort_records(records):
        key = (str(record.get("config_version")), str(record.get("config_hash")))
        grouped.setdefault(key, []).append(record)
    rows: List[List[Any]] = []
    for (version, config_hash) in sorted(grouped):
        entries = grouped[(version, config_hash)]
        rows.append(
            [
                version,
                config_hash,
                entries[0].get("spec_version"),
                entries[0].get("evaluation_timestamp"),
                len(entries),
                "; ".join(sorted({str(e.get("ipo_id")) for e in entries})),
            ]
        )
    return headers, rows


def _rows_run_log(records: Sequence[Mapping[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "evaluation_id",
        "ipo_id",
        "mode",
        "evaluation_timestamp",
        "engine_version",
        "spec_version",
        "config_version",
        "status",
        "validation_status",
        "error_count",
        "warning_count",
        "errors",
        "errors_detail",
        "warnings_detail",
        "result_hash",
    ]
    rows: List[List[Any]] = []
    for record in _sort_records(records):
        validation = record.get("validation") or {}
        errors = validation.get("errors", [])
        warnings = validation.get("warnings", [])
        rows.append(
            [
                record.get("evaluation_id"),
                record.get("ipo_id"),
                record.get("evaluation_mode"),
                record.get("evaluation_timestamp"),
                record.get("engine_version"),
                record.get("spec_version"),
                record.get("config_version"),
                "COMPLETED",
                "PASSED" if not errors else "FAILED",
                len(errors),
                len(warnings),
                "; ".join(e.get("code", "") for e in errors),
                " | ".join(f"{e.get('code')}: {e.get('message')}" for e in errors),
                " | ".join(
                    f"{w.get('code')}: {w.get('message')}" for w in warnings
                ),
                record.get("result_hash"),
            ]
        )
    return headers, rows


SHEET_BUILDERS: Dict[str, Callable[[Sequence[Mapping[str, Any]]], Tuple[List[str], List[List[Any]]]]] = {
    "IPO_Master": _rows_ipo_master,
    "Evaluations": _rows_evaluations,
    "Module_Scores": _rows_module_scores,
    "Criteria_Detail": _rows_criteria_detail,
    "Knockouts": _rows_knockouts,
    "Penalties": _rows_penalties,
    "Missing_Unverified": _rows_missing_unverified,
    "Evidence": _rows_evidence,
    "Market_Snapshots": _rows_market_snapshots,
    "Peer_Snapshots": _rows_peer_snapshots,
    "Post_Listing": _rows_post_listing,
    "Backtest": _rows_backtest,
    "Config_Versions": _rows_config_versions,
    "Run_Log": _rows_run_log,
}

EMPTY_SHEET_HEADERS: Dict[str, List[str]] = {
    "IPO_Master": ["ipo_id", "company_name", "latest_evaluation_id", "latest_score", "latest_verdict"],
    "Evaluations": ["evaluation_id", "ipo_id", "mode", "score", "verdict", "result_hash"],
    "Module_Scores": ["evaluation_id", "module_id", "score", "max"],
    "Criteria_Detail": ["evaluation_id", "criterion_id", "state", "score", "max"],
    "Knockouts": ["evaluation_id", "rule_id", "state", "missing_inputs"],
    "Penalties": ["evaluation_id", "penalty_id", "points", "state"],
    "Missing_Unverified": ["evaluation_id", "category", "item", "state"],
    "Evidence": ["evaluation_id", "source_id", "evidence_id", "locator"],
    "Market_Snapshots": ["evaluation_id", "block", "status", "as_of"],
    "Peer_Snapshots": ["evaluation_id", "peer_name", "status", "pe"],
    "Post_Listing": ["evaluation_id", "listing_date", "listing_gain_pct"],
    "Backtest": ["evaluation_id", "score", "outcome_6m_vs_nifty_pct"],
    "Config_Versions": ["config_version", "config_hash", "evaluation_count"],
    "Run_Log": ["evaluation_id", "status", "validation_status"],
}


@dataclass
class ProjectionResult:
    path: Path
    evaluations: int
    sheet_counts: Mapping[str, int]
    content_hash: str


def build_workbook(
    records: Union[Mapping[str, Any], Sequence[Mapping[str, Any]]],
    *,
    title: str = "IPO Screening History",
) -> Workbook:
    """Build the workbook in memory from evaluation records.

    Accepts either one record or a sequence of them. Passing a bare mapping is
    normalised deliberately: without this, a single record would iterate over
    its *keys* and every sheet would silently come out empty.
    """
    if isinstance(records, Mapping):
        records = [records]
    records = list(records)
    workbook = Workbook()
    workbook.remove(workbook.active)

    for sheet_name in SHEET_ORDER:
        worksheet = workbook.create_sheet(sheet_name)
        builder = SHEET_BUILDERS[sheet_name]
        headers, rows = builder(records)
        if not headers:
            headers = EMPTY_SHEET_HEADERS[sheet_name]
        _write_sheet(worksheet, headers, rows)
        if sheet_name in ("Evidence", "Market_Snapshots", "Peer_Snapshots"):
            for row in worksheet.iter_rows(min_row=2):
                for cell in row:
                    cell.fill = _EVIDENCE_FILL

    workbook.properties.title = title
    workbook.properties.creator = f"IPO Screening Engine v{ENGINE_VERSION}"
    workbook.properties.description = (
        "Generated from immutable evaluation records. Excel is a projection, not the "
        "authoritative store (spec v1.5 s3.6)."
    )
    workbook.properties.created = FIXED_TIMESTAMP
    workbook.properties.modified = FIXED_TIMESTAMP
    workbook.properties.lastModifiedBy = f"IPO Screening Engine v{ENGINE_VERSION}"
    workbook.properties.revision = "1"
    return workbook


def project(
    store: EvaluationStore,
    output_path: str | Path,
) -> ProjectionResult:
    """Regenerate the workbook from every record in the store."""
    records = store.read_all()
    workbook = build_workbook(records)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(target)
    counts = {
        name: max(0, workbook[name].max_row - 1) for name in SHEET_ORDER
    }
    with target.open("rb") as handle:
        content_hash = sha256_of({"bytes": handle.read().hex()})
    return ProjectionResult(
        path=target,
        evaluations=len(records),
        sheet_counts=counts,
        content_hash=content_hash,
    )


def workbook_bytes(records: Sequence[Mapping[str, Any]]) -> bytes:
    """Serialise the workbook to bytes (used by the determinism tests)."""
    workbook = build_workbook(records)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def build_missing_unverified_rows(record: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Collect every missing or unverified item for the Missing_Unverified sheet.

    Covers unknown criteria, unverified knockouts, non-valid peers, unusable
    market blocks and unresolved penalties, each with the points it affects.
    """
    rows: List[Dict[str, Any]] = []
    score = record.get("score") or {}

    for module in score.get("modules", []):
        for criterion in module.get("criteria", []):
            if criterion.get("state") == "UNKNOWN":
                rows.append(
                    {
                        "category": "CRITERION",
                        "item": criterion.get("criterion_id"),
                        "detail": criterion.get("reason"),
                        "points_affected": criterion.get("max"),
                        "state": "UNKNOWN",
                    }
                )
            elif criterion.get("state") == "NOT_APPLICABLE":
                rows.append(
                    {
                        "category": "CRITERION",
                        "item": criterion.get("criterion_id"),
                        "detail": criterion.get("reason"),
                        "points_affected": 0,
                        "state": "NOT_APPLICABLE",
                    }
                )

    for result in (record.get("knockouts") or {}).get("results", []):
        if result.get("state") == "UNVERIFIED":
            rows.append(
                {
                    "category": "KNOCKOUT",
                    "item": result.get("rule_id"),
                    "detail": result.get("explanation"),
                    "points_affected": 0,
                    "state": "UNVERIFIED",
                }
            )

    for peer in (record.get("peer_snapshot") or {}).get("observations", []):
        if peer.get("status") != "VALID":
            rows.append(
                {
                    "category": "PEER",
                    "item": peer.get("name"),
                    "detail": peer.get("reason"),
                    "points_affected": None,
                    "state": peer.get("status"),
                }
            )

    for block in (record.get("market_snapshot") or {}).get("blocks", []):
        if block.get("status") != "FRESH":
            rows.append(
                {
                    "category": "MARKET",
                    "item": block.get("block"),
                    "detail": block.get("reason"),
                    "points_affected": None,
                    "state": block.get("status"),
                }
            )

    for penalty in record.get("penalties", []):
        if penalty.get("state") == "UNKNOWN":
            rows.append(
                {
                    "category": "PENALTY",
                    "item": penalty.get("id"),
                    "detail": penalty.get("reason"),
                    "points_affected": None,
                    "state": "UNKNOWN",
                }
            )

    for entry in (score.get("completeness_breakdown") or {}).get("critical_data_missing", []):
        rows.append(
            {
                "category": "CRITICAL_DATA",
                "item": entry,
                "detail": "critical input required for a safe verdict is UNKNOWN",
                "points_affected": None,
                "state": "UNKNOWN",
            }
        )

    return rows


__all__ = [
    "SHEET_ORDER",
    "SHEET_BUILDERS",
    "ProjectionResult",
    "build_workbook",
    "project",
    "workbook_bytes",
    "build_missing_unverified_rows",
]
