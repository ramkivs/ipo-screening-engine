"""GMP evidence-linkage verifier (A9 policy record §7; decisions L1, L2-a, L3-a, L4-a).

A successful link shows only that one evaluation's ``market.gmp`` values tie to
retained evidence: the pinned manifest and artifact bytes, the displayed value,
the publisher stamp and the title line. It does not prove source-native
authenticity, perfect transcription, an independently authenticated capture
time, or publisher qualification. It never qualifies a source. A9 stays
fail-closed for every result.

Input: the evaluated document's ``market.gmp`` and ``company_name``, the
registry ``sources`` and ``evidence`` entries (as the A15 record carries them),
and the evaluation timestamp. The verifier never reads from the input file, so
it checks the final assembled values that were scored.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple

from .gmp_evidence import (
    DisplayedGmpState,
    GmpEvidenceError,
    capture_obtained_by,
    classify_displayed_gmp,
    load_rendered_capture_from_manifest,
    parse_manifest_bytes,
)
from .gmp_policy import explicit_offset_instant

LINK_DIAGNOSTIC_CODE = "A9_GMP_EVIDENCE_LINK"
WRITE_ONCE_MARKER_KEY = "writeOnce"  # must be JSON true; see the report that defines it
EVIDENCE_ROOT_REL = "evidence/gmp-observations"
EVIDENCE_ID_PREFIX = "EV-"
REQUIRED_PATHS = ("company_name", "market.gmp.pct", "market.gmp.as_of")
TREND_PATH = "market.gmp.trend"
GMP_PATHS = REQUIRED_PATHS + (TREND_PATH,)
PUBLISHER_TZ = timezone(timedelta(hours=5, minutes=30))  # IST, fixed offset as the publisher shows

RESULT_VERIFIED = "VERIFIED"
RESULT_NOT_AVAILABLE_BY_CUTOFF = "NOT_AVAILABLE_BY_CUTOFF"
RESULT_FAILED = "FAILED"

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]

_PIN = re.compile(r"sha256:([0-9a-f]{64})")
_LINE = re.compile(r"line ([1-9][0-9]*)")
_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_NAME_SUFFIX = re.compile(r" (limited|ltd)$")


@dataclass(frozen=True)
class LinkEvidence:
    """One ``_evidence`` or registry entry, normalised to its canonical ID."""

    evidence_id: str
    path: str
    source_id: Any
    locator: Any
    quote: Any
    problem: Optional[str]


@dataclass(frozen=True)
class GmpLinkResult:
    """Outcome of one link attempt. Never a qualification; A9 stays fail-closed."""

    result: str
    reasons: Tuple[str, ...]
    source_id: str
    manifest_path: Optional[str] = None
    manifest_sha256: Optional[str] = None
    artifact_id: Optional[str] = None
    artifact_path: Optional[str] = None
    artifact_sha256: Optional[str] = None
    window_source_text: Optional[str] = None  # "<notBefore>/<notAfter>", copied from the manifest
    d1_label: Optional[str] = None
    displayed_state: Optional[str] = None
    evidence_ids: Tuple[str, ...] = ()
    digests_verified: bool = False

    @property
    def message(self) -> str:
        parts = [f"Result: {self.result}."]
        if self.reasons:
            parts.append("Reason: " + "; ".join(self.reasons) + ".")
        if self.d1_label:
            parts.append(f"D1: {self.d1_label}")
        if self.displayed_state:
            parts.append(f"D3 state: {self.displayed_state}.")
        if self.digests_verified:
            parts.append(
                f"Manifest {self.manifest_path} SHA-256 {self.manifest_sha256}; "
                f"artifact {self.artifact_path} SHA-256 {self.artifact_sha256}."
            )
        if self.window_source_text:
            parts.append(f"Capture window (UTC, not an exact receipt time): {self.window_source_text}.")
        parts.append("Linkage shows only that the values tie to the retained evidence; A9 stays fail-closed.")
        return " ".join(parts)


def canonical_evidence_id(path: str) -> str:
    return EVIDENCE_ID_PREFIX + path


def normalise_evidence(entries: Iterable[Tuple[str, Mapping[str, Any]]]) -> List[LinkEvidence]:
    """Normalise ``(key, entry)`` pairs from ``_evidence`` or from the registry.

    A key that already has the ``EV-`` prefix is a registry ID. Any other key is a
    field path from the input's ``_evidence`` map. An explicit ``evidence_id`` must
    equal the canonical ID, and a ``quote`` must agree with ``quoted_text``.
    """
    out: List[LinkEvidence] = []
    for key, item in entries:
        key = str(key)
        if key.startswith(EVIDENCE_ID_PREFIX):
            canonical, path = key, key[len(EVIDENCE_ID_PREFIX):]
        else:
            canonical, path = canonical_evidence_id(key), key
        if not isinstance(item, Mapping):
            out.append(LinkEvidence(canonical, path, None, None, None, "evidence entry is not an object"))
            continue
        problem = None
        explicit = item.get("evidence_id")
        if explicit is not None and explicit != canonical:
            problem = f"explicit evidence_id {explicit!r} must equal the canonical {canonical!r}"
        quote = item.get("quoted_text", item.get("quote"))
        if "quote" in item and "quoted_text" in item and item["quote"] != item["quoted_text"]:
            problem = problem or "quote and quoted_text disagree"
        out.append(LinkEvidence(canonical, path, item.get("source_id"), item.get("locator"), quote, problem))
    return out


def entries_from_input_evidence(evidence_map: Any) -> List[Tuple[str, Mapping[str, Any]]]:
    """Pairs ``(path, entry)`` from an input document's ``_evidence`` map."""
    if not isinstance(evidence_map, Mapping):
        return []
    return [(key, value) for key, value in evidence_map.items()]


def entries_from_registry(items: Any) -> List[Tuple[str, Mapping[str, Any]]]:
    """Pairs ``(evidence_id, entry)`` from an A15 record's evidence list."""
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        return []
    pairs: List[Tuple[str, Mapping[str, Any]]] = []
    for item in items:
        if isinstance(item, Mapping) and isinstance(item.get("evidence_id"), str):
            pairs.append((item["evidence_id"], item))
    return pairs


def _is_evidence_uri(uri: Any) -> bool:
    return isinstance(uri, str) and (uri.startswith("evidence/") or "#" in uri)


def _exact_token_count(line: str, token: str) -> int:
    """Count exact occurrences of a displayed token, not substrings of a longer number."""
    if not token:
        return 0
    left = r"(?<![0-9])(?<![0-9]\.)" if token[0].isdigit() else ""
    right = r"(?!\.?[0-9])" if token[-1].isdigit() else ""
    return len(re.findall(left + re.escape(token) + right, line))


def render_publisher_stamp(instant: datetime) -> str:
    """The MarketLiveIPOGMP stamp form, ``h:mm am/pm IST on Ddd, D Mon, YYYY``."""
    ist = instant.astimezone(PUBLISHER_TZ)
    hour12 = ist.hour % 12 or 12
    meridiem = "am" if ist.hour < 12 else "pm"
    return (
        f"{hour12}:{ist.minute:02d} {meridiem} IST on {_DAYS[ist.weekday()]}, "
        f"{ist.day} {_MONTHS[ist.month - 1]}, {ist.year}"
    )


def _name_key(text: str) -> str:
    normalised = re.sub(r"[\W_]+", " ", text.casefold()).strip()
    return _NAME_SUFFIX.sub("", normalised)


def _title_name(line: str) -> Optional[str]:
    """Text between ``# `` and the first ``IPO GMP`` in the title line."""
    if not line.startswith("# "):
        return None
    end = line.find("IPO GMP")
    return line[2:end] if end >= 0 else None


def _is_plain_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def verify_gmp_linkage(
    *,
    market_gmp: Any,
    company_name: Any,
    sources: Sequence[Mapping[str, Any]],
    evidence: Sequence[LinkEvidence],
    evaluation_timestamp: Any,
    repo_root: Optional[Path] = None,
) -> Optional[GmpLinkResult]:
    """Verify one evaluation's GMP link. ``None`` means no link is attempted.

    A link is attempted only when ``market.gmp.source_id`` names a ``_sources``
    entry whose ``uri`` points into the evidence tree. Every other input stays
    unchanged (A9 ``SOURCE_UNQUALIFIED`` or ``MISSING``, no diagnostic).
    """
    gmp = market_gmp if isinstance(market_gmp, Mapping) else {}
    source_id = gmp.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        return None
    matches = [item for item in sources if isinstance(item, Mapping) and item.get("source_id") == source_id]
    if not any(_is_evidence_uri(item.get("uri")) for item in matches):
        return None

    root = (repo_root or DEFAULT_REPO_ROOT).resolve()
    evidence_root = (root / EVIDENCE_ROOT_REL).resolve()
    ev_ids: Tuple[str, ...] = ()
    state: dict = {"manifest_path": None, "manifest_sha": None, "artifact_id": None, "artifact_path": None,
                   "artifact_sha": None, "window": None, "label": None, "digests": False, "state": None}

    def fail(reason: str) -> GmpLinkResult:
        return _result(RESULT_FAILED, (reason,))

    def _result(outcome: str, reasons: Tuple[str, ...]) -> GmpLinkResult:
        return GmpLinkResult(
            result=outcome,
            reasons=reasons,
            source_id=source_id,
            manifest_path=state["manifest_path"],
            manifest_sha256=state["manifest_sha"],
            artifact_id=state["artifact_id"],
            artifact_path=state["artifact_path"],
            artifact_sha256=state["artifact_sha"],
            window_source_text=state["window"],
            d1_label=state["label"],
            displayed_state=state["state"],
            evidence_ids=ev_ids,
            digests_verified=state["digests"],
        )

    # 1. Location
    if len(matches) != 1:
        return fail(f"source {source_id!r} must be exactly one _sources entry (found {len(matches)})")
    source = matches[0]
    if source.get("source_type") != "MARKET_DATA":
        return fail("linked _sources entry must have source_type MARKET_DATA")
    if source.get("retrieval_timestamp") is not None:
        return fail("retrieval_timestamp is present, but the manifest records no exact receipt time")
    pin_match = _PIN.fullmatch(source.get("content_hash") or "") if isinstance(source.get("content_hash"), str) else None
    if pin_match is None:
        return fail("content_hash must be 'sha256:' followed by 64 lowercase hex digits")
    uri = source.get("uri")
    path_part, separator, artifact_id = (uri.partition("#") if isinstance(uri, str) else ("", "", ""))
    if (
        not separator
        or not artifact_id
        or "#" in artifact_id
        or not path_part.startswith(EVIDENCE_ROOT_REL + "/")
        or not path_part.endswith(".json")
        or "\\" in path_part
        or ".." in path_part.split("/")
        or "://" in path_part
    ):
        return fail("uri must be an evidence manifest path '<evidence/gmp-observations/...json>#<artifact id>'")
    manifest_file = (root / path_part).resolve()
    if evidence_root not in manifest_file.parents or not manifest_file.is_file():
        return fail("manifest is missing or lies outside evidence/gmp-observations")
    state["manifest_path"] = manifest_file.relative_to(root).as_posix()
    state["artifact_id"] = artifact_id

    # 2. Manifest pin: the same bytes are hashed and parsed
    raw = manifest_file.read_bytes()
    manifest_sha = hashlib.sha256(raw).hexdigest()
    state["manifest_sha"] = manifest_sha
    if manifest_sha != pin_match.group(1):
        return fail("content_hash does not equal the SHA-256 of the manifest bytes (edited or shifted manifest)")
    try:
        manifest = parse_manifest_bytes(manifest_file, raw)
    except GmpEvidenceError as exc:
        return fail(str(exc))
    if manifest.get(WRITE_ONCE_MARKER_KEY) is not True:
        return fail("manifest has no write-once marker; existing manifests are ineligible for linkage")

    # 3. D1 integrity of the artifact, using the hashed manifest
    try:
        capture = load_rendered_capture_from_manifest(manifest_file, manifest, artifact_id)
    except GmpEvidenceError as exc:
        return fail(str(exc))
    state["label"] = capture.label
    state["artifact_path"] = (manifest_file.parent / capture.artifact_file).resolve().relative_to(root).as_posix()
    state["artifact_sha"] = capture.computed_sha256.lower() if capture.computed_sha256 else None
    if not capture.integrity_verified:
        return fail("artifact is missing or does not match its declared byte count and SHA-256")
    state["digests"] = True

    # 4. Window (interval only; never an exact receipt time)
    entry = next(item for item in manifest["artifacts"] if item.get("id") == artifact_id)
    window = entry.get("retrievalWindowUtc") if isinstance(entry.get("retrievalWindowUtc"), Mapping) else {}
    before_raw, after_raw = window.get("notBefore"), window.get("notAfter")
    if isinstance(before_raw, str) and isinstance(after_raw, str):
        state["window"] = f"{before_raw}/{after_raw}"
    if capture.retrieved_not_after is None or capture.retrieved_not_before is None:
        return fail("retrieval window is missing, inverted or has no explicit UTC offset")
    if capture.text is None:
        return fail("artifact is not UTF-8 text")
    lines = capture.text.split("\n")

    # 5. Evidence binding: exactly one canonical entry per required path, all for S
    by_id: dict = {}
    for item in evidence:
        if item.problem and (item.source_id == source_id or item.path in GMP_PATHS):
            return fail(f"{item.evidence_id}: {item.problem}")
        if item.source_id == source_id and item.path not in REQUIRED_PATHS:
            return fail(f"{item.evidence_id} is not a permitted evidence entry for the linked source")
        if item.path in GMP_PATHS and item.source_id != source_id:
            return fail(f"{item.evidence_id} is attributed to another source")
        if item.source_id == source_id:
            by_id.setdefault(item.evidence_id, []).append(item)
    for path in REQUIRED_PATHS:
        cid = canonical_evidence_id(path)
        found = by_id.get(cid, [])
        if not found:
            return fail(f"missing evidence entry {cid} for the linked source")
        if len(found) > 1:
            return fail(f"contradictory duplicate evidence entries for {cid}")
    ev_ids = tuple(canonical_evidence_id(path) for path in REQUIRED_PATHS)
    name_ev, pct_ev, asof_ev = (by_id[cid][0] for cid in ev_ids)

    # 6. Trend and pct: no trend label; pct must be a value bound exactly to its line
    if gmp.get("trend") is not None:
        return fail("market.gmp.trend is non-null, but the publisher publishes no trend labels")
    pct = gmp.get("pct")
    if pct is None:
        return fail("market.gmp.pct is null; a linked observation must carry a bound value")
    if not _is_plain_number(pct):
        return fail("market.gmp.pct is not a finite number")
    pct_line = _line_text(lines, pct_ev.locator)
    if pct_line is None:
        return fail("pct locator must name a line of the verified artifact")
    pct_quote = pct_ev.quote.strip() if isinstance(pct_ev.quote, str) else ""
    pct_state, pct_amount = classify_displayed_gmp(pct_quote, unit="%")
    state["state"] = pct_state.value
    if pct_state not in (DisplayedGmpState.AMOUNT, DisplayedGmpState.ZERO):
        return fail("pct quote is not a percentage (rupee, malformed or 'Not quoted yet' cannot link a value)")
    if pct_amount is None or pct_amount != float(pct):
        return fail("pct quote does not equal market.gmp.pct")
    if _exact_token_count(pct_line, pct_quote) != 1:
        return fail("pct quote is not exactly one token on its locator line")

    # 7. Stamp (L3-a): as_of is the publisher stamp, bounded by the window end
    asof_line = _line_text(lines, asof_ev.locator)
    if asof_line is None:
        return fail("as_of locator must name a line of the verified artifact")
    as_of = gmp.get("as_of")
    as_of_instant = explicit_offset_instant(as_of) if isinstance(as_of, str) else None
    if as_of_instant is None:
        return fail("market.gmp.as_of must carry an explicit UTC offset")
    if as_of_instant.second or as_of_instant.microsecond:
        return fail("market.gmp.as_of has sub-minute precision that the publisher stamp does not show")
    stamp = asof_ev.quote.strip() if isinstance(asof_ev.quote, str) else ""
    if stamp != render_publisher_stamp(as_of_instant):
        return fail("as_of quote is not the publisher stamp for market.gmp.as_of")
    if _exact_token_count(asof_line, stamp) != 1:
        return fail("as_of stamp is not exactly one sentence on its locator line")
    if as_of_instant > capture.retrieved_not_after:
        return fail("market.gmp.as_of is later than the window end")

    # 8. Identity (L3-a): the title line names the evaluated issue
    if _line_text(lines, name_ev.locator) != lines[0] or not isinstance(company_name, str) or not company_name.strip():
        return fail("company_name evidence must quote line 1 and the input must name the company")
    if (name_ev.quote if isinstance(name_ev.quote, str) else "").strip() != lines[0].strip():
        return fail("company_name quote is not the title line")
    title = _title_name(lines[0].strip())
    if title is None or _name_key(title) != _name_key(company_name):
        return fail("title line names a different issue than company_name")

    # 9. Cutoff (D2): the window end must not be after the evaluation
    evaluation_at = explicit_offset_instant(evaluation_timestamp) if isinstance(evaluation_timestamp, str) else None
    if evaluation_at is None or not capture_obtained_by(capture, evaluation_at):
        return _result(
            RESULT_NOT_AVAILABLE_BY_CUTOFF,
            ("the capture window ends after the evaluation timestamp, the evaluation falls inside the window, "
             "or the evaluation timestamp has no timezone",),
        )
    return _result(RESULT_VERIFIED, ())


def _line_text(lines: Sequence[str], locator: Any) -> Optional[str]:
    if not isinstance(locator, str):
        return None
    match = _LINE.fullmatch(locator)
    if match is None:
        return None
    index = int(match.group(1)) - 1
    return lines[index] if 0 <= index < len(lines) else None


__all__ = [
    "DEFAULT_REPO_ROOT",
    "GmpLinkResult",
    "LINK_DIAGNOSTIC_CODE",
    "LinkEvidence",
    "RESULT_FAILED",
    "RESULT_NOT_AVAILABLE_BY_CUTOFF",
    "RESULT_VERIFIED",
    "WRITE_ONCE_MARKER_KEY",
    "canonical_evidence_id",
    "entries_from_input_evidence",
    "entries_from_registry",
    "normalise_evidence",
    "render_publisher_stamp",
    "verify_gmp_linkage",
]
