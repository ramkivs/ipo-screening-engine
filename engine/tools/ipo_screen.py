#!/usr/bin/env python3
"""Command-line runner for the IPO Screening Engine v1.5.

Usage
-----
    export PYTHONPATH=engine

    # Evaluate an input and print a one-screen report.
    python3 engine/tools/ipo_screen.py run fixtures/vishal_nirmiti/input.json

    # Freeze a Final evaluation into the store and refresh the workbook.
    python3 engine/tools/ipo_screen.py run input.json \\
        --mode final --at 2026-10-05T12:00:00Z \\
        --store build/evaluations \\
        --workbook build/IPO_Screening_History.xlsx

    # Re-run a stored evaluation from its frozen artifacts and compare hashes.
    python3 engine/tools/ipo_screen.py replay VISHAL-NIRMITI-LIMITED-20261005-120000Z-final-e84f8bc0 \\
        --store build/evaluations

    # Verify every artifact hash in the store.
    python3 engine/tools/ipo_screen.py verify --store build/evaluations

    # Rebuild the workbook from the store (Excel is a projection only).
    python3 engine/tools/ipo_screen.py project --store build/evaluations \\
        --workbook build/IPO_Screening_History.xlsx

    # Check the configuration without evaluating anything.
    python3 engine/tools/ipo_screen.py check-config

Design notes
------------
* The engine never guesses a timestamp. When ``--at`` is omitted the wall
  clock is used and the run is *not* reproducible against a different instant,
  so a material change in the market snapshot can change the result. Pass
  ``--at`` to pin it.
* Exit codes: 0 success, 1 validation/configuration failure (the run was
  refused), 2 usage error, 3 an audit mismatch was found.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):  # allow `python3 engine/tools/ipo_screen.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ipo_screening.config_validation import check_config, compile_config  # noqa: E402
from ipo_screening.errors import EngineError  # noqa: E402
from ipo_screening.evaluation import EvaluationStore  # noqa: E402
from ipo_screening.excel import SHEET_ORDER, project  # noqa: E402
from ipo_screening.pipeline import load_config, replay  # noqa: E402
from ipo_screening.version import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    SPEC_VERSION,
)
from ipo_screening.pipeline import evaluate  # noqa: E402

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2
EXIT_AUDIT_MISMATCH = 3


# --------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------


def parse_instant(text: str | None) -> datetime:
    """Parse ``--at``. Accepts ISO 8601 with or without a trailing ``Z``."""
    if not text:
        return datetime.now(timezone.utc)
    cleaned = text.strip().replace("Z", "+00:00")
    try:
        moment = datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"--at must be an ISO 8601 instant (e.g. 2026-10-05T12:00:00Z), got {text!r}"
        ) from exc
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def fmt_score(value: float | None) -> str:
    return "   n/a" if value is None else f"{value:6.1f}"


def rule(char: str = "-", width: int = 78) -> str:
    return char * width


def print_run_report(outcome, *, verbose: bool) -> None:
    record = outcome.record
    score = record.score
    breakdown = score.get("completeness_breakdown") or {}

    print(rule("="))
    print(f"  {record.company_name}  ({record.ipo_id})")
    print(f"  {record.evaluation_id}")
    print(rule("="))
    print(f"  Mode                {record.evaluation_mode}")
    print(f"  Evaluated at        {record.evaluation_timestamp}")
    print(f"  Engine / spec       {record.engine_version} / {record.spec_version}")
    print(f"  Config              {record.config_version} ({record.config_hash[:12]})")
    print()
    print(f"  Final score         {fmt_score(score.get('final_score'))}  (base "
          f"{fmt_score(score.get('base_score'))}, penalties "
          f"{score.get('penalties_total')})")
    print(f"  Score range         {fmt_score(score.get('lower_bound'))} to "
          f"{fmt_score(score.get('upper_bound'))}")
    print(f"  Verdict             {record.verdict.get('verdict')}"
          + (f"  [{record.verdict.get('mode_label')}]" if record.verdict.get("mode_label") else ""))
    print(f"  Confidence          {record.confidence.get('level')} "
          f"({score.get('completeness_pct')}% of evaluable points available)")
    print(f"  Knockouts           {record.knockouts.get('status')}"
          + (f"  ({', '.join(record.knockouts.get('unverified_knockouts') or [])})"
             if record.knockouts.get("unverified_knockouts") else ""))
    print()
    print("  Module scores")
    for module in score.get("modules", []):
        available = module.get("available_points")
        unknown = module.get("unknown_points")
        print(f"    {module['module_id']}  {module['name']:<38} "
              f"{fmt_score(module.get('score'))} / {module.get('max'):<5.0f} "
              f"[{available:g} known, {unknown:g} unknown]")
    print()
    print("  Data completeness")
    print(f"    overall                {breakdown.get('overall_pct')}%")
    print(f"    valuation              {breakdown.get('valuation_pct')}%")
    print(f"    market                 {breakdown.get('market_pct')}%")
    print(f"    critical data          {breakdown.get('critical_data_pct')}%")
    print(f"    knockouts              {breakdown.get('knockout_completeness_pct')}%")
    if breakdown.get("critical_data_missing"):
        print(f"    missing critical       {', '.join(breakdown['critical_data_missing'])}")

    warnings = record.validation.get("warnings") or []
    if warnings:
        print()
        print(f"  Validation warnings ({len(warnings)})")
        for item in warnings[: 8 if not verbose else len(warnings)]:
            print(f"    {item.get('code')}: {item.get('message')[:150]}")
        if not verbose and len(warnings) > 8:
            print(f"    ... {len(warnings) - 8} more (use --verbose)")

    if verbose:
        print()
        print("  Knockout detail")
        for knockout in record.knockouts.get("results", []):
            print(f"    {knockout['rule_id']}  {knockout['state']:<11} {knockout['label'][:44]}")
            if knockout.get("missing"):
                print(f"        missing: {', '.join(knockout['missing'])}")

        print()
        print("  Top strengths")
        for item in outcome.top_strengths(5):
            print(f"    {item['criterion_id']:<26} {item['score']:g}/{item['max']:g}  "
                  f"{item['reason'][:60]}")
        print()
        print("  Top risks")
        for item in outcome.top_risks(5):
            print(f"    {item['id']:<26} {item['impact']:g}  {item['label'][:52]}")

    print()
    print(f"  Result hash         {record.result_hash}")
    print(f"  Input snapshot      {record.input_snapshot_hash[:32]}")
    print(f"  Source manifest     {record.source_manifest_hash[:32]}")
    print(f"  Market snapshot     {record.market_snapshot_hash[:32]}")
    print(f"  Peer snapshot       {record.peer_snapshot_hash[:32]}")
    if outcome.stored_at:
        print(f"  Stored at           {outcome.stored_at}")
    if outcome.workbook_path:
        print(f"  Workbook            {outcome.workbook_path}")
    print(rule("="))


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def cmd_run(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input not found: {input_path}", file=sys.stderr)
        return EXIT_USAGE
    with input_path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    config = load_config(args.config)
    store = EvaluationStore(args.store) if args.store else None

    moment = parse_instant(args.at)
    if not args.at:
        print(
            "note: no --at supplied, so the evaluation instant is the wall clock; the result "
            "hash will move if market data crosses a freshness boundary. Pass --at to pin it.",
            file=sys.stderr,
        )

    outcome = evaluate(
        document,
        config,
        mode=args.mode,
        evaluation_datetime=moment,
        store=store,
        workbook_path=args.workbook,
    )
    print_run_report(outcome, verbose=args.verbose)
    return EXIT_OK


def cmd_replay(args: argparse.Namespace) -> int:
    store = EvaluationStore(args.store)
    if not store.exists(args.evaluation_id):
        print(f"error: no stored evaluation {args.evaluation_id!r} under {args.store}", file=sys.stderr)
        return EXIT_USAGE
    stored_record = store.read(args.evaluation_id)
    replayed = replay(store, args.evaluation_id, load_config(args.config))
    stored_hash = str(stored_record.get("result_hash"))
    recomputed = replayed.record.result_hash
    match = stored_hash == recomputed

    print(f"evaluation        {args.evaluation_id}")
    print(f"replayed at       {replayed.record.evaluation_timestamp} (the original instant)")
    print(f"stored result     {stored_hash}")
    print(f"recomputed        {recomputed}")
    print(f"match             {match}")

    stored_score = stored_record.get("score") or {}
    for field in ("final_score", "base_score", "lower_bound", "upper_bound",
                  "completeness_pct", "verdict"):
        before = stored_score.get(field, (stored_record.get("verdict") or {}).get(field))
        after = replayed.record.score.get(field, replayed.record.verdict.get(field))
        if before != after:
            print(f"  differs        {field}: stored {before!r} != recomputed {after!r}")
    return EXIT_OK if match else EXIT_AUDIT_MISMATCH


def cmd_verify(args: argparse.Namespace) -> int:
    store = EvaluationStore(args.store)
    ids = store.list_evaluations()
    if not ids:
        print(f"no evaluations found under {args.store}")
        return EXIT_OK

    failures = 0
    for evaluation_id in ids:
        report = store.verify_hashes(evaluation_id)
        ok = report["result_hash_matches"] and not report["artifact_mismatches"]
        marker = "OK  " if ok else "FAIL"
        print(f"{marker} {evaluation_id}  artifacts={report['artifacts_verified']}")
        if not report["result_hash_matches"]:
            failures += 1
            print(f"       stored     {report['stored_result_hash']}")
            print(f"       recomputed {report['recomputed_result_hash']}")
        for mismatch in report["artifact_mismatches"]:
            failures += 1
            print(f"       {mismatch['artifact']} expected {mismatch['expected'][:16]} "
                  f"actual {mismatch['actual'][:16]}")
    print()
    print(f"{len(ids)} evaluation(s) checked, {failures} mismatch(es)")
    return EXIT_OK if failures == 0 else EXIT_AUDIT_MISMATCH


def cmd_project(args: argparse.Namespace) -> int:
    store = EvaluationStore(args.store)
    result = project(store, args.workbook)
    print(f"workbook           {result.path}")
    print(f"evaluations        {result.evaluations}")
    print(f"content hash       {result.content_hash}")
    print()
    print("sheets (rows of data)")
    for name in SHEET_ORDER:
        print(f"  {name:<22} {result.sheet_counts.get(name, 0)}")
    return EXIT_OK


def cmd_check_config(args: argparse.Namespace) -> int:
    raw = json.loads(Path(args.config).read_text(encoding="utf-8"))
    report = check_config(raw)
    print(f"config             {args.config}")
    print(f"spec version       {raw.get('spec_version')} (engine supports {SPEC_VERSION})")
    print(f"valid              {report.ok}")
    print(f"profiles resolved  {len(report.profile_plans)}")
    for name, plan in sorted(report.profile_plans.items()):
        maxima = plan.get("module_maxima") or {}
        modules = " ".join(f"{key}={value:g}" for key, value in sorted(maxima.items()))
        print(f"  {name:<28} {plan['total']:g} points  [{modules}]")
    if report.errors:
        print()
        print(f"errors ({len(report.errors)})")
        for finding in report.errors:
            print(f"  {finding.code}: {finding.message}")
    if report.warnings:
        print()
        print(f"warnings ({len(report.warnings)})")
        for finding in report.warnings:
            print(f"  {finding.code}: {finding.message}")
    if not report.ok:
        return EXIT_REFUSED
    # Compiling proves the fingerprint can be taken, i.e. the config is loadable.
    compile_config(raw)
    return EXIT_OK


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ipo_screen",
        description="IPO Screening Engine v1.5 runner (spec v1.5).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default=None,
        help=f"path to the executable policy JSON (default: {DEFAULT_CONFIG_PATH})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="evaluate an input document")
    run.add_argument("input", help="path to the canonical input JSON")
    run.add_argument("--mode", default="final",
                     choices=["preliminary", "final", "post_listing_1w",
                              "post_listing_1m", "post_listing_6m"],
                     help="evaluation mode (default: final)")
    run.add_argument("--at", default=None,
                     help="evaluation instant, ISO 8601 (default: the wall clock)")
    run.add_argument("--store", default=None, help="evaluation store root; omit to skip persistence")
    run.add_argument("--workbook", default=None, help="path to IPO_Screening_History.xlsx")
    run.add_argument("--verbose", "-v", action="store_true", help="show every warning and detail")
    run.set_defaults(func=cmd_run)

    rep = sub.add_parser("replay", help="re-run a stored evaluation from its frozen artifacts")
    rep.add_argument("evaluation_id")
    rep.add_argument("--store", required=True)
    rep.set_defaults(func=cmd_replay)

    ver = sub.add_parser("verify", help="re-derive and check every stored artifact hash")
    ver.add_argument("--store", required=True)
    ver.set_defaults(func=cmd_verify)

    pro = sub.add_parser("project", help="rebuild the Excel workbook from the store")
    pro.add_argument("--store", required=True)
    pro.add_argument("--workbook", required=True)
    pro.set_defaults(func=cmd_project)

    chk = sub.add_parser("check-config", help="validate the policy configuration")
    chk.set_defaults(func=cmd_check_config)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.config is None:
        args.config = str(Path(__file__).resolve().parents[2] / DEFAULT_CONFIG_PATH)
    try:
        return int(args.func(args))
    except EngineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        for finding in getattr(exc, "findings", []) or []:
            location = f" [{finding.location}]" if finding.location else ""
            print(f"  {finding.code}{location}: {finding.message}", file=sys.stderr)
        return EXIT_REFUSED
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
