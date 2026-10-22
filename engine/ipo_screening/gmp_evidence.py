"""Approved GMP source-policy decisions D1-D3, §7 linkage and A28 trend extension.

Decision record: ``docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md`` §§6-7.

* **D1 - evidence artifact and hash.** A retained rendered-text capture plus the
  SHA-256 of its exact file bytes is acceptable only as a clearly labelled
  publisher-reported observation. The hash attests the integrity of the retained
  file. It does not authenticate the publisher, prove source-native bytes or
  verify a dealer quote, and a rendered capture is never described as raw or
  source-native evidence. The artifact and hash follow the existing evidence
  convention: ``capture-manifest.json`` declares each retained file, its byte
  count, its uppercase SHA-256 and the UTC window bracketing its retrieval.
* **D2 - availability by cutoff.** A capture supports an evaluation only if it had
  been obtained at or before the evaluation timestamp. The exact capture instant
  is not recorded (the manifests state ``exactReceiptTimeCaptured: false``); the
  manifest records only a UTC window bracketing the retrieval. The window end is
  therefore the latest possible capture time, not the capture time, and it is used
  only as an upper bound: the rule is proven when the window ends at or before the
  evaluation timestamp. An evaluation inside the window is not proven and fails
  closed. A publisher's displayed or site-wide update time is never used as
  capture time, so a later capture of an earlier-stamped reading never supports
  an earlier evaluation. As with A17-1, both instants need an explicit UTC
  offset; otherwise the check fails closed.
* **D3 - missing versus zero.** The exact display "Not quoted yet" is ``MISSING``.
  A displayed zero (₹0) is ``SOURCE_UNQUALIFIED``: a numeric zero alone is never
  qualifying evidence. A display that is not a well-formed amount is rejected
  rather than coerced into an observation.

Nothing here qualifies a source. D1-D3 and the §7 linkage establish only that
one evaluated observation is tied to particular retained local bytes, text and a
capture window. They do not authenticate the publisher, qualify a source, or
alter A9: Final remains withheld for every GMP observation. Existing v1.5
``_sources``/``_evidence`` fields carry the link; historical and unlinked inputs
remain unchanged.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence, Tuple, Union
from urllib.parse import urlsplit

from .gmp_policy import explicit_offset_instant
from .json_strict import DuplicateJSONKeyError, loads_strict_json

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

#: D1 evidence class of a retained rendered-text capture of a publisher page.
PUBLISHER_REPORTED_RENDERED_CAPTURE = "PUBLISHER_REPORTED_RENDERED_CAPTURE"

#: D3: the exact publisher display that maps to MISSING (MarketLiveIPOGMP).
NOT_QUOTED_YET = "Not quoted yet"

#: The A9 nonterminal reason codes; no D1-D3 outcome is terminal.
A9_MISSING = "MISSING"
A9_SOURCE_UNQUALIFIED = "SOURCE_UNQUALIFIED"

RUPEE = "₹"
PERCENT = "%"

_NUMBER = r"\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?"
_RUPEE_AMOUNT = re.compile(rf"^(?P<lead>[+-])?\s*₹\s*(?P<trail>[+-])?\s*(?P<number>{_NUMBER})$")
_PERCENT_AMOUNT = re.compile(rf"^(?P<lead>[+-])?\s*(?P<number>{_NUMBER})\s*%$")
_SHA256_HEX = re.compile(r"^[0-9A-Fa-f]{64}$")


class GmpEvidenceError(ValueError):
    """A capture manifest or artifact declaration that D1 does not accept."""


class DisplayedGmpState(str, Enum):
    """D3 classification of one displayed GMP value."""

    MISSING = "MISSING"  # "Not quoted yet", or no value supplied
    ZERO = "ZERO"  # a displayed zero: SOURCE_UNQUALIFIED, never qualifying
    AMOUNT = "AMOUNT"  # a well-formed non-zero amount: a candidate only
    MALFORMED = "MALFORMED"  # anything else: rejected, never an observation


# --------------------------------------------------------------------------
# D3 - missing versus zero
# --------------------------------------------------------------------------


def _parse_displayed_amount(text: str, unit: str) -> Optional[float]:
    try:
        return float(text)  # a plain number, as the connector already accepts
    except ValueError:
        pass
    match = (_RUPEE_AMOUNT if unit == RUPEE else _PERCENT_AMOUNT).match(text)
    if match is None:
        return None
    groups = match.groupdict()
    signs = [sign for sign in (groups.get("lead"), groups.get("trail")) if sign]
    if len(signs) > 1:
        return None
    magnitude = float(groups["number"].replace(",", ""))
    return -magnitude if signs == ["-"] else magnitude


def classify_displayed_gmp(value: Any, *, unit: str = RUPEE) -> Tuple[DisplayedGmpState, Optional[float]]:
    """D3: classify one displayed GMP value and return ``(state, amount)``.

    ``unit`` is ``"₹"`` for the premium or ``"%"`` for the premium over the issue
    price. The amount is returned only for ``ZERO`` (0.0) and ``AMOUNT``.
    ``None`` means no value was supplied and is ``MISSING``. The text must be
    exactly "Not quoted yet" (surrounding whitespace aside) to be ``MISSING``.
    """
    if unit not in (RUPEE, PERCENT):
        raise ValueError(f"unsupported GMP unit {unit!r}")
    if value is None:
        return DisplayedGmpState.MISSING, None
    if isinstance(value, bool):
        return DisplayedGmpState.MALFORMED, None
    if isinstance(value, (int, float, Decimal)):
        amount: Optional[float] = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if text == NOT_QUOTED_YET:
            return DisplayedGmpState.MISSING, None
        amount = _parse_displayed_amount(text, unit)
    else:
        amount = None
    if amount is None or not math.isfinite(amount):
        return DisplayedGmpState.MALFORMED, None
    if amount == 0:
        return DisplayedGmpState.ZERO, 0.0
    return DisplayedGmpState.AMOUNT, amount


def a9_reason_for(state: DisplayedGmpState) -> str:
    """Map a D3 state onto the A9 nonterminal reasons.

    ``MISSING`` stays ``MISSING``. ``ZERO`` and ``MALFORMED`` are
    ``SOURCE_UNQUALIFIED``. ``AMOUNT`` is also ``SOURCE_UNQUALIFIED`` today: it is
    the only state that could ever qualify, and only after every other
    requirement passes through an A9 qualified path that does not exist.
    """
    return A9_MISSING if state is DisplayedGmpState.MISSING else A9_SOURCE_UNQUALIFIED


# --------------------------------------------------------------------------
# D1 - evidence artifact and hash
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RenderedGmpCapture:
    """D1: one retained rendered-text capture of a publisher page.

    Built only by :func:`load_rendered_capture` from an existing capture manifest.
    """

    manifest_path: Path
    artifact_id: str
    url: str
    artifact_file: str
    declared_sha256: str
    declared_bytes: int
    computed_sha256: Optional[str]
    integrity_verified: bool
    retrieved_not_before: Optional[datetime]
    retrieved_not_after: Optional[datetime]
    text: Optional[str] = field(default=None, repr=False, compare=False)
    manifest_sha256: Optional[str] = None
    retrieved_not_before_text: Optional[str] = None
    retrieved_not_after_text: Optional[str] = None

    #: D1 evidence class; deliberately not a constructor argument.
    evidence_class = PUBLISHER_REPORTED_RENDERED_CAPTURE

    @property
    def is_source_native(self) -> bool:
        """D1: a rendered capture is never raw provider bytes or source-native evidence."""
        return False

    @property
    def authenticates_publisher(self) -> bool:
        """D1: the file hash attests the retained file, not the publisher's identity."""
        return False

    @property
    def verifies_dealer_quote(self) -> bool:
        """D1: a publisher-reported observation is never a dealer-verified quote."""
        return False

    @property
    def hash_subject(self) -> str:
        return f"exact bytes of the retained file {self.artifact_file} declared in {self.manifest_path.name}"

    @property
    def label(self) -> str:
        return (
            f"Publisher-reported GMP observation: rendered-text capture of {self.url}, "
            "not provider response bytes. Its SHA-256 attests the integrity of the "
            "retained file only; it does not authenticate the publisher or verify a "
            "dealer quote."
        )


def _parse_manifest_bytes(data: bytes, path: Path) -> Mapping[str, Any]:
    """Parse exactly the bytes supplied, rejecting duplicate keys at every depth."""
    try:
        parsed = loads_strict_json(data.decode("utf-8"))
    except DuplicateJSONKeyError as exc:
        raise GmpEvidenceError(f"duplicate JSON key in capture manifest: {exc.key!r}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GmpEvidenceError(f"capture manifest {path.name} is not valid UTF-8 JSON") from exc
    if not isinstance(parsed, Mapping):
        raise GmpEvidenceError(f"capture manifest {path.name} must be a JSON object")
    return parsed


def _load_rendered_capture_from_manifest(
    path: Path,
    manifest: Mapping[str, Any],
    artifact_id: str,
    *,
    manifest_sha256: Optional[str] = None,
) -> RenderedGmpCapture:
    """Load one declared artifact without rereading or reparsing its manifest."""
    method = manifest.get("captureMethod")
    if not isinstance(method, Mapping) or method.get("rawProviderResponseBytesCaptured") is not False:
        raise GmpEvidenceError(
            "D1 covers only a retained rendered-text capture, and this manifest does not "
            "declare one (captureMethod.rawProviderResponseBytesCaptured must be false)"
        )
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise GmpEvidenceError(f"capture manifest {path.name} has no artifacts array")
    entries = [item for item in artifacts if isinstance(item, Mapping) and item.get("id") == artifact_id]
    if not entries:
        raise GmpEvidenceError(f"artifact {artifact_id!r} is not declared in {path.name}")
    if len(entries) > 1:
        # Two declarations would let one reference resolve to either file.
        raise GmpEvidenceError(f"artifact {artifact_id!r} is declared more than once in {path.name}")
    entry = entries[0]
    # A recorded acquisition failure is not missing GMP, displayed zero or a
    # publisher withdrawal. Unknown legacy status is not upgraded to success.
    if entry.get("toolResultStatus") not in (None, "success"):
        raise GmpEvidenceError("capture failed: retrieval tool did not report success")

    file_name = entry.get("file")
    declared = entry.get("sha256")
    size = entry.get("bytes")
    if (
        not isinstance(file_name, str)
        or not file_name
        or "\\" in file_name
        or not isinstance(declared, str)
        or not _SHA256_HEX.fullmatch(declared)
        or not isinstance(size, int)
        or isinstance(size, bool)
        or size < 0
    ):
        raise GmpEvidenceError(
            f"artifact {artifact_id!r} does not declare a retained file, byte count and SHA-256"
        )
    relative_artifact = PurePosixPath(file_name)
    if (
        relative_artifact.is_absolute()
        or any(part in {"", ".", ".."} for part in file_name.split("/"))
        or relative_artifact.as_posix() != file_name
    ):
        raise GmpEvidenceError(f"artifact {artifact_id!r} has a non-canonical relative file path")
    root = path.parent.resolve()
    artifact = (root / Path(*relative_artifact.parts)).resolve()
    if root not in artifact.parents:
        raise GmpEvidenceError(f"artifact {artifact_id!r} lies outside the manifest's directory")

    try:
        data = artifact.read_bytes() if artifact.is_file() else None
    except OSError:
        data = None
    computed = hashlib.sha256(data).hexdigest().upper() if data is not None else None
    verified = data is not None and len(data) == size and computed == declared.upper()
    text: Optional[str] = None
    if verified and data is not None:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None
    # The documented PD response is a successful TOOL rendering of an error
    # page, not a GMP observation. This is deliberately not an HTML/DOM parser
    # or a claim that arbitrary error pages can be recognized heuristically.
    if text is not None and text.lstrip().startswith("# Temporarily unavailable"):
        raise GmpEvidenceError("capture failed: temporary-unavailability page")

    window = entry.get("retrievalWindowUtc")
    window = window if isinstance(window, Mapping) else {}
    not_before_text = window.get("notBefore")
    not_after_text = window.get("notAfter")
    not_before = explicit_offset_instant(not_before_text)
    not_after = explicit_offset_instant(not_after_text)
    if not_before is None or not_after is None or not_after < not_before:
        not_before = not_after = None

    url = entry.get("url")
    return RenderedGmpCapture(
        manifest_path=path,
        artifact_id=artifact_id,
        url=url if isinstance(url, str) else "",
        artifact_file=file_name,
        declared_sha256=declared.upper(),
        declared_bytes=size,
        computed_sha256=computed,
        integrity_verified=verified,
        retrieved_not_before=not_before,
        retrieved_not_after=not_after,
        text=text,
        manifest_sha256=manifest_sha256,
        retrieved_not_before_text=not_before_text if isinstance(not_before_text, str) else None,
        retrieved_not_after_text=not_after_text if isinstance(not_after_text, str) else None,
    )


def load_rendered_capture(manifest_path: Union[str, Path], artifact_id: str) -> RenderedGmpCapture:
    """D1: read one declared artifact from a capture manifest and verify its hash.

    The manifest file is read once and parsed strictly from those same bytes.
    Duplicate JSON keys, including duplicate retrieval-window or hash members,
    are rejected before a cutoff or artifact-integrity decision can be made.
    Raises :class:`GmpEvidenceError` unless the manifest declares a rendered-text
    capture and exactly one matching artifact. A missing or altered artifact is
    represented by ``integrity_verified=False``. Retrieval-window bounds without
    explicit offsets, or an inverted window, establish no retrieval window.
    """
    path = Path(manifest_path)
    try:
        manifest_bytes = path.read_bytes()
    except OSError as exc:
        raise GmpEvidenceError(f"capture manifest {path.name} could not be read") from exc
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    manifest = _parse_manifest_bytes(manifest_bytes, path)
    return _load_rendered_capture_from_manifest(
        path,
        manifest,
        artifact_id,
        manifest_sha256=manifest_sha256,
    )


# --------------------------------------------------------------------------
# D2 - availability by cutoff
# --------------------------------------------------------------------------


def capture_obtained_by(capture: RenderedGmpCapture, evaluation_at: datetime) -> bool:
    """D2: True only if the capture had been obtained at or before ``evaluation_at``.

    The exact capture instant is unknown; it lies somewhere in the recorded
    retrieval window. The window end is the latest possible capture time and is
    used only as an upper bound: if it is at or before ``evaluation_at``, the
    capture was obtained in time. An evaluation that falls inside the window, or
    one without a timezone, cannot establish that, so the result is ``False``.
    """
    obtained = capture.retrieved_not_after
    if obtained is None or not isinstance(evaluation_at, datetime):
        return False
    if evaluation_at.tzinfo is None or evaluation_at.utcoffset() is None:
        return False
    return obtained <= evaluation_at


# --------------------------------------------------------------------------
# D1-D3 together
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class GmpCaptureAssessment:
    """D1-D3 applied to one capture for one evaluation timestamp. Never a qualification."""

    capture: RenderedGmpCapture
    evaluation_at: datetime
    displayed_text: str
    displayed_state: DisplayedGmpState
    displayed_amount: Optional[float]
    displayed_in_capture: bool
    obtained_by_cutoff: bool

    @property
    def eligible_for_cutoff_consideration(self) -> bool:
        """D1, D2 and D3 all pass for this evaluation.

        This is not qualification. Every other requirement still applies, and the
        A9 gate has no qualified path, so :attr:`a9_reason` stays nonterminal.
        """
        return (
            self.capture.integrity_verified
            and self.displayed_in_capture
            and self.obtained_by_cutoff
            and self.displayed_state is DisplayedGmpState.AMOUNT
        )

    @property
    def a9_reason(self) -> str:
        return a9_reason_for(self.displayed_state)


def assess_capture(
    capture: RenderedGmpCapture,
    displayed_text: str,
    *,
    evaluation_at: datetime,
    unit: str = RUPEE,
) -> GmpCaptureAssessment:
    """Apply D1-D3 to the GMP value displayed in ``capture`` for one evaluation.

    ``displayed_text`` is the value as it appears in the retained capture, for
    example ``"₹500"`` or ``"Not quoted yet"``. It must occur in the verified
    file. That is a consistency check, not proof that it is the reading the page
    meant.
    """
    state, amount = classify_displayed_gmp(displayed_text, unit=unit)
    shown = (
        isinstance(displayed_text, str)
        and bool(displayed_text.strip())
        and capture.text is not None
        and displayed_text.strip() in capture.text
    )
    return GmpCaptureAssessment(
        capture=capture,
        evaluation_at=evaluation_at,
        displayed_text=displayed_text,
        displayed_state=state,
        displayed_amount=amount,
        displayed_in_capture=shown,
        obtained_by_cutoff=capture_obtained_by(capture, evaluation_at),
    )


# --------------------------------------------------------------------------
# §7 - evaluation-to-capture evidence linkage (never A9 qualification)
# --------------------------------------------------------------------------


GMP_LINK_DIAGNOSTIC_CODE = "A9_GMP_EVIDENCE_LINK"
GMP_LINK_EVIDENCE_FIELDS = (
    ("company_name", "EV-company_name"),
    ("market.gmp.pct", "EV-market.gmp.pct"),
    ("market.gmp.as_of", "EV-market.gmp.as_of"),
)
GMP_LINK_OPTIONAL_EVIDENCE_FIELDS = (("market.gmp.trend", "EV-market.gmp.trend"),)


def _link_fields(trend):
    return GMP_LINK_EVIDENCE_FIELDS + (GMP_LINK_OPTIONAL_EVIDENCE_FIELDS if trend is not None else ())


_LINK_LOCATOR = re.compile(r"^line ([1-9][0-9]*)$")
# Locate whole signed percentage tokens only. Adjoining alphanumerics, decimal
# punctuation, percent signs, and sign-like characters block subtoken matches.
_PERCENT_TOKEN = re.compile(
    rf"(?<![\w.,%+\-\u2010-\u2015\u2212\uFE62\uFE63\uFF0B\uFF0D])"
    rf"(?P<token>[+-]?\s*(?:{_NUMBER})\s*%)"
    rf"(?![\w.,%+\-\u2010-\u2015\u2212\uFE62\uFE63\uFF0B\uFF0D])"
)
_SHA256_PIN = re.compile(r"^sha256:([0-9A-Fa-f]{64})$")
_PUBLISHER_STAMP = re.compile(
    r"^(?P<hour>1[0-2]|[1-9]):(?P<minute>[0-5][0-9]) "
    r"(?P<ampm>am|pm) IST on (?P<weekday>Mon|Tue|Wed|Thu|Fri|Sat|Sun), "
    r"(?P<day>[1-9]|[12][0-9]|3[01]) "
    r"(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec), "
    r"(?P<year>[0-9]{4})$"
)
_IST = timezone(timedelta(hours=5, minutes=30))
_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}
_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


@dataclass(frozen=True)
class GmpEvidenceLinkVerification:
    """Result of L1-L4 linkage checks; VERIFIED is not qualification."""

    status: str
    reason: str
    source_id: Optional[str] = None
    manifest_uri: Optional[str] = None
    manifest_path: Optional[str] = None
    artifact_path: Optional[str] = None
    artifact_id: Optional[str] = None
    manifest_sha256: Optional[str] = None
    artifact_sha256: Optional[str] = None
    d1_label: str = PUBLISHER_REPORTED_RENDERED_CAPTURE
    d3_state: str = DisplayedGmpState.MALFORMED.value
    retrieval_window_utc: Optional[str] = None
    evidence_refs: Tuple[str, ...] = ()
    manifest_verified: bool = False
    artifact_verified: bool = False
    rejected_retrieval_timestamp: bool = False
    expected_company_name: Optional[str] = field(default=None, repr=False, compare=False)
    expected_pct: Any = field(default=None, repr=False, compare=False)
    expected_as_of: Any = field(default=None, repr=False, compare=False)
    expected_trend: Any = field(default=None, repr=False, compare=False)
    capture: Optional[RenderedGmpCapture] = field(default=None, repr=False, compare=False)

    @property
    def is_verified(self) -> bool:
        return self.status == "VERIFIED"

    @property
    def diagnostic_result(self) -> str:
        if self.status == "FAILED":
            return f"FAILED: {self.reason}"
        return self.status

    @property
    def diagnostic_message(self) -> str:
        return (
            "GMP rendered-evidence link: "
            f"result={self.diagnostic_result}; "
            f"reason={self.reason}; "
            f"source_id={self.source_id or 'UNKNOWN'}; "
            f"artifact_id={self.artifact_id or 'UNKNOWN'}; "
            f"D1_label={self.d1_label}; "
            f"D3_state={self.d3_state}; "
            f"manifest_sha256={self.manifest_sha256 or 'UNKNOWN'}; "
            f"artifact_sha256={self.artifact_sha256 or 'UNKNOWN'}; "
            f"retrieval_window_utc={self.retrieval_window_utc or 'UNKNOWN'}; "
            "exact_receipt_time=UNKNOWN. This local-byte link is not publisher "
            "authentication or A9 qualification."
        )


def capture_gmp_linkage_context(input_document: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """Copy only the raw L1 fields when an input attempts a manifest linkage.

    Ordinary tracker/reference-fixture inputs are deliberately not link attempts;
    their historic behavior and A15 projection remain unchanged.
    """
    market = input_document.get("market")
    gmp = market.get("gmp") if isinstance(market, Mapping) else None
    if not isinstance(gmp, Mapping):
        return None
    source_id = gmp.get("source_id")
    raw_sources = input_document.get("_sources")
    source_rows = raw_sources if isinstance(raw_sources, (list, tuple)) else ()
    uri_attempt = any(
        isinstance(item, Mapping)
        and isinstance(item.get("uri"), str)
        and "evidence/gmp-observations/" in item.get("uri", "")
        for item in source_rows
    )
    id_attempt = isinstance(source_id, str) and source_id.startswith("GMP-OBS-")
    if not (uri_attempt or id_attempt):
        return None

    import copy

    return {
        "company_name": copy.deepcopy(input_document.get("company_name")),
        "market_gmp": copy.deepcopy(dict(gmp)),
        "sources": copy.deepcopy(raw_sources),
        "evidence": copy.deepcopy(input_document.get("_evidence")),
    }


def _link_result(
    reason: str,
    *,
    source_id: Optional[str] = None,
    manifest_uri: Optional[str] = None,
    manifest_path: Optional[str] = None,
    artifact_path: Optional[str] = None,
    artifact_id: Optional[str] = None,
    manifest_sha256: Optional[str] = None,
    artifact_sha256: Optional[str] = None,
    d1_label: str = PUBLISHER_REPORTED_RENDERED_CAPTURE,
    d3_state: str = DisplayedGmpState.MALFORMED.value,
    retrieval_window_utc: Optional[str] = None,
    evidence_refs: Sequence[str] = (),
    manifest_verified: bool = False,
    artifact_verified: bool = False,
    rejected_retrieval_timestamp: bool = False,
    expected_company_name: Optional[str] = None,
    expected_pct: Any = None,
    expected_as_of: Any = None,
    expected_trend: Any = None,
    capture: Optional[RenderedGmpCapture] = None,
    status: str = "FAILED",
) -> GmpEvidenceLinkVerification:
    return GmpEvidenceLinkVerification(
        status=status,
        reason=reason,
        source_id=source_id,
        manifest_uri=manifest_uri,
        manifest_path=manifest_path,
        artifact_path=artifact_path,
        artifact_id=artifact_id,
        manifest_sha256=manifest_sha256,
        artifact_sha256=artifact_sha256,
        d1_label=d1_label,
        d3_state=d3_state,
        retrieval_window_utc=retrieval_window_utc,
        evidence_refs=tuple(sorted(set(evidence_refs))),
        manifest_verified=manifest_verified,
        artifact_verified=artifact_verified,
        rejected_retrieval_timestamp=rejected_retrieval_timestamp,
        expected_company_name=expected_company_name,
        expected_pct=expected_pct,
        expected_as_of=expected_as_of,
        expected_trend=expected_trend,
        capture=capture,
    )


def _repository_manifest_path(uri: Any, repo_root: Path) -> Tuple[Path, str, str]:
    if not isinstance(uri, str) or not uri:
        raise GmpEvidenceError("manifest URI is missing")
    parsed = urlsplit(uri)
    if parsed.scheme or parsed.netloc or parsed.query or not parsed.path or not parsed.fragment:
        raise GmpEvidenceError("manifest URI must be a repository-relative path followed by #artifact-id")
    if uri.count("#") != 1 or "%" in parsed.path or "\\" in parsed.path:
        raise GmpEvidenceError("manifest URI is not a canonical repository-relative reference")
    relative = PurePosixPath(parsed.path)
    if (
        relative.is_absolute()
        or not parsed.path.startswith("evidence/gmp-observations/")
        or any(part in {"", ".", ".."} for part in relative.parts)
        or relative.as_posix() != parsed.path
    ):
        raise GmpEvidenceError("manifest URI must stay under evidence/gmp-observations/ with no traversal")
    artifact_id = parsed.fragment
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", artifact_id):
        raise GmpEvidenceError("manifest URI has a malformed artifact id")
    root = repo_root.resolve()
    manifest_path = (root / Path(*relative.parts)).resolve()
    if root not in manifest_path.parents:
        raise GmpEvidenceError("manifest URI resolves outside the repository")
    return manifest_path, parsed.path, artifact_id


def _manifest_write_once_eligible(
    manifest_path: Path,
    repo_root: Path,
    manifest_bytes: bytes,
) -> Tuple[bool, str]:
    """Require a complete, clean Git history with one commit for the manifest."""
    try:
        relative = manifest_path.resolve().relative_to(repo_root.resolve()).as_posix()
        shallow = subprocess.run(
            ["git", "rev-parse", "--is-shallow-repository"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if shallow.returncode != 0 or shallow.stdout.strip() != "false":
            return False, "manifest history is shallow or cannot be established"
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", relative],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if status.returncode != 0 or status.stdout.strip():
            return False, "manifest is modified or not committed"
        history = subprocess.run(
            ["git", "log", "--follow", "--format=%H", "--", relative],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if history.returncode != 0:
            return False, "manifest history cannot be established"
        commits = [line for line in history.stdout.splitlines() if line.strip()]
        if len(commits) != 1:
            return False, "manifest is not write-once in repository history"
        committed = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            timeout=5,
        )
        if committed.returncode != 0 or committed.stdout != manifest_bytes:
            return False, "manifest bytes differ from the committed write-once version"
    except (OSError, subprocess.SubprocessError, ValueError):
        return False, "manifest history cannot be established"
    return True, ""


def _publisher_url_identity(manifest: Mapping[str, Any], artifact_id: str) -> Tuple[str, str]:
    publisher = manifest.get("publisherIssuePage")
    if not isinstance(publisher, Mapping):
        raise GmpEvidenceError("manifest publisherIssuePage is missing")
    issue_url = publisher.get("url")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise GmpEvidenceError("manifest artifacts array is missing")
    matches = [item for item in artifacts if isinstance(item, Mapping) and item.get("id") == artifact_id]
    if len(matches) != 1:
        raise GmpEvidenceError("manifest artifact id is missing or duplicated")
    artifact_url = matches[0].get("url")
    if not isinstance(issue_url, str) or not isinstance(artifact_url, str):
        raise GmpEvidenceError("publisher and artifact URLs must both be declared")
    issue = urlsplit(issue_url)
    artifact = urlsplit(artifact_url)
    try:
        invalid_port = issue.port is not None or artifact.port is not None
    except ValueError as exc:
        raise GmpEvidenceError("publisher or artifact URL contains an invalid port") from exc
    if (
        issue.scheme != "https"
        or artifact.scheme != "https"
        or not issue.hostname
        or not artifact.hostname
        or issue.username is not None
        or issue.password is not None
        or artifact.username is not None
        or artifact.password is not None
        or invalid_port
        or issue.query
        or issue.fragment
        or artifact.query
        or artifact.fragment
        or issue.hostname.lower() != artifact.hostname.lower()
        or issue.path != artifact.path
    ):
        raise GmpEvidenceError("publisher-host or issue-URL identity does not match the declared artifact")
    return issue_url, str(publisher.get("displayedIssueName") or "")


def _exact_quote(spec: Any, *, path: str, source_id: str, evidence_id: str) -> Tuple[str, str]:
    if not isinstance(spec, Mapping):
        raise GmpEvidenceError(f"evidence entry {path!r} is missing")
    declared_evidence_id = spec.get("evidence_id")
    if declared_evidence_id not in (None, "") and declared_evidence_id != evidence_id:
        raise GmpEvidenceError(f"evidence entry {path!r} must bind canonical id {evidence_id}")
    if spec.get("source_id") != source_id:
        raise GmpEvidenceError(f"evidence entry {path!r} is not bound to source {source_id!r}")
    if spec.get("extraction_method", "MANUAL_ENTRY") != "MANUAL_ENTRY":
        raise GmpEvidenceError(f"evidence entry {path!r} must use MANUAL_ENTRY")
    locator = spec.get("locator")
    match = _LINK_LOCATOR.fullmatch(locator) if isinstance(locator, str) else None
    if match is None:
        raise GmpEvidenceError(f"evidence entry {path!r} must use locator 'line <n>'")
    quote = spec.get("quote")
    quoted_text = spec.get("quoted_text")
    if quote is not None and quoted_text is not None and quote != quoted_text:
        raise GmpEvidenceError(f"evidence entry {path!r} has contradictory quote aliases")
    if quote is None:
        quote = quoted_text
    if not isinstance(quote, str) or not quote or quote != quote.strip():
        raise GmpEvidenceError(f"evidence entry {path!r} must contain exact, non-empty displayed text")
    return match.group(1), quote


def _normalize_issue_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
    words = normalized.split()
    if words and words[-1] in {"limited", "ltd"}:
        words.pop()
    return " ".join(words)


def _publisher_stamp_instant(stamp: str) -> Optional[datetime]:
    match = _PUBLISHER_STAMP.fullmatch(stamp)
    if match is None:
        return None
    values = match.groupdict()
    hour = int(values["hour"]) % 12
    if values["ampm"] == "pm":
        hour += 12
    try:
        local = datetime(
            int(values["year"]),
            _MONTHS[values["month"]],
            int(values["day"]),
            hour,
            int(values["minute"]),
            tzinfo=_IST,
        )
    except (KeyError, ValueError):
        return None
    if _WEEKDAYS[local.weekday()] != values["weekday"]:
        return None
    return local


def _decimal_number(value: Any) -> Optional[Decimal]:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def _registered_evidence(record: Any) -> Mapping[str, Mapping[str, Any]]:
    evidence = getattr(record, "evidence", {}) or {}
    rows = evidence.get("evidence", []) if isinstance(evidence, Mapping) else []
    return {
        str(item.get("evidence_id")): item
        for item in rows
        if isinstance(item, Mapping) and isinstance(item.get("evidence_id"), str)
    }


def _record_market_gmp(record: Any) -> Optional[Mapping[str, Any]]:
    snapshot = getattr(record, "market_snapshot", {}) or {}
    blocks = snapshot.get("blocks", []) if isinstance(snapshot, Mapping) else []
    if not isinstance(blocks, (list, tuple)):
        return None
    for block in blocks:
        if isinstance(block, Mapping) and block.get("block") == "gmp":
            return block
    return None


def _stable_link_manifest_digest_id(source_id: Optional[str]) -> str:
    value = hashlib.sha256((source_id or "").encode("utf-8")).hexdigest()[:20]
    return f"source-content-hash-{value}"


def _stable_link_artifact_digest_id(source_id: Optional[str], artifact_id: Optional[str]) -> str:
    subject = f"{source_id or ''}\0{artifact_id or ''}"
    value = hashlib.sha256(subject.encode("utf-8")).hexdigest()[:20]
    return f"gmp-rendered-artifact-{value}"


def verify_gmp_evidence_link(
    context: Mapping[str, Any],
    record: Any,
    *,
    evaluation_at: Any,
    repo_root: Union[str, Path] = REPOSITORY_ROOT,
) -> GmpEvidenceLinkVerification:
    """Apply the §7 L1/L2-a/L3-a/L4-a checks to one attempted GMP link.

    The manifest is read once, hashed once, and parsed from those exact bytes.
    All later D1 checks use the declared artifact bytes loaded by that parsed
    manifest. Every input-link failure is returned as a diagnostic result; it
    does not reject the evaluation or alter A9/scoring.
    """
    root = Path(repo_root).resolve()
    market_gmp = context.get("market_gmp")
    market_gmp = market_gmp if isinstance(market_gmp, Mapping) else {}
    link_fields = _link_fields(market_gmp.get("trend"))
    source_id_value = market_gmp.get("source_id")
    source_id = source_id_value if isinstance(source_id_value, str) and source_id_value else None
    evidence_map = context.get("evidence")
    evidence_map = evidence_map if isinstance(evidence_map, Mapping) else {}
    registered = _registered_evidence(record)
    available_refs = tuple(
        evidence_id
        for _path, evidence_id in link_fields
        if evidence_id in registered
    )

    raw_sources = context.get("sources")
    sources = raw_sources if isinstance(raw_sources, (list, tuple)) else ()
    matches = [
        source
        for source in sources
        if isinstance(source, Mapping) and source.get("source_id") == source_id
    ]
    manifest_uri = matches[0].get("uri") if len(matches) == 1 else None
    rejected_retrieval_timestamp = any(
        isinstance(source, Mapping)
        and source.get("source_id") == source_id
        and "retrieval_timestamp" in source
        for source in sources
    )
    try:
        if source_id is None:
            raise GmpEvidenceError("market.gmp.source_id is missing")
        if len(matches) != 1:
            raise GmpEvidenceError("source_id must identify exactly one _sources entry")
        source = matches[0]
        if source.get("source_type") != "MARKET_DATA":
            raise GmpEvidenceError("linked source_type must be MARKET_DATA")
        if "retrieval_timestamp" in source:
            raise GmpEvidenceError(
                "retrieval_timestamp must be absent when exactReceiptTimeCaptured is false"
            )
        pin = source.get("content_hash")
        pin_match = _SHA256_PIN.fullmatch(pin) if isinstance(pin, str) else None
        if pin_match is None:
            raise GmpEvidenceError("content_hash must be sha256:<64-hex manifest digest>")
        manifest_path, manifest_relative, artifact_id = _repository_manifest_path(manifest_uri, root)
        manifest_uri = str(manifest_uri)
        try:
            manifest_bytes = manifest_path.read_bytes()
        except OSError as exc:
            raise GmpEvidenceError("capture manifest could not be read") from exc
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        if manifest_sha256.lower() != pin_match.group(1).lower():
            raise GmpEvidenceError("manifest SHA-256 does not match the source content_hash pin")
        manifest = _parse_manifest_bytes(manifest_bytes, manifest_path)
        capture = _load_rendered_capture_from_manifest(
            manifest_path,
            manifest,
            artifact_id,
            manifest_sha256=manifest_sha256,
        )
        d1_label = capture.label
        artifact_path = (PurePosixPath(manifest_relative).parent / capture.artifact_file).as_posix()
        artifact_sha256 = (
            capture.computed_sha256.lower()
            if isinstance(capture.computed_sha256, str)
            else None
        )
        window_text = None
        if (
            capture.retrieved_not_before is not None
            and capture.retrieved_not_after is not None
            and capture.retrieved_not_before_text
            and capture.retrieved_not_after_text
        ):
            window_text = f"{capture.retrieved_not_before_text}/{capture.retrieved_not_after_text}"
        manifest_verified, history_reason = _manifest_write_once_eligible(
            manifest_path,
            root,
            manifest_bytes,
        )
        artifact_verified = capture.integrity_verified
        if not manifest_verified:
            raise GmpEvidenceError(history_reason)
        if not artifact_verified or capture.text is None:
            raise GmpEvidenceError("declared artifact byte count or SHA-256 does not match its actual bytes")

        method = manifest.get("captureMethod")
        if not isinstance(method, Mapping) or method.get("exactReceiptTimeCaptured") is not False:
            raise GmpEvidenceError("manifest does not explicitly state exactReceiptTimeCaptured: false")
        if not capture.retrieved_not_before or not capture.retrieved_not_after or not window_text:
            raise GmpEvidenceError("manifest retrieval window is missing, offset-less, or inverted")
        _issue_url, displayed_issue_name = _publisher_url_identity(manifest, artifact_id)

        evidence_details: dict[str, Tuple[int, str]] = {}
        required_paths = {path for path, _evidence_id in link_fields}
        required_ids = {evidence_id for _path, evidence_id in link_fields}
        for path, spec in evidence_map.items():
            if (
                path not in required_paths
                and isinstance(spec, Mapping)
                and spec.get("evidence_id") in required_ids
            ):
                raise GmpEvidenceError("a canonical GMP evidence id is reused for a different input field")
        if market_gmp.get("trend") is None and "market.gmp.trend" in evidence_map:
            raise GmpEvidenceError("absent market.gmp.trend cannot hide asserted trend evidence")
        lines = capture.text.splitlines()
        if market_gmp.get("trend") is None and any(line.startswith("Trend: ") for line in lines):
            raise GmpEvidenceError("absent market.gmp.trend cannot hide a displayed publisher label")
        for field_path, evidence_id in link_fields:
            line_text, quote = _exact_quote(
                evidence_map.get(field_path),
                path=field_path,
                source_id=source_id,
                evidence_id=evidence_id,
            )
            line_number = int(line_text)
            if line_number > len(lines):
                raise GmpEvidenceError(f"evidence locator for {field_path!r} is outside the artifact")
            evidence_details[field_path] = (line_number, quote)
            spec = evidence_map.get(field_path)
            registered_quote = None
            if isinstance(spec, Mapping):
                registered_quote = (
                    spec.get("quote")
                    if spec.get("quote") is not None
                    else spec.get("quoted_text")
                )
            registered_item = registered.get(evidence_id)
            if (
                not isinstance(registered_item, Mapping)
                or registered_item.get("source_id") != source_id
                or registered_item.get("locator") != f"line {line_number}"
                or registered_item.get("quoted_text") != registered_quote
                or registered_item.get("extraction_method") != "MANUAL_ENTRY"
            ):
                raise GmpEvidenceError(f"registered evidence for {field_path!r} differs from the link input")
        if set(available_refs) != {evidence_id for _path, evidence_id in link_fields}:
            raise GmpEvidenceError("all required canonical GMP linkage evidence objects must be registered")

        company_name = context.get("company_name")
        if not isinstance(company_name, str) or not company_name:
            raise GmpEvidenceError("company_name is missing or malformed")
        if (
            not isinstance(displayed_issue_name, str)
            or _normalize_issue_name(displayed_issue_name) != _normalize_issue_name(company_name)
        ):
            raise GmpEvidenceError("manifest displayed issue name does not match company_name")
        company_line_number, company_quote = evidence_details["company_name"]
        title_line = lines[company_line_number - 1]
        if company_line_number != 1 or company_quote != title_line:
            raise GmpEvidenceError("company_name quote is not the exact line-1 capture title")
        if not title_line.startswith("# ") or title_line.count("IPO GMP") != 1:
            raise GmpEvidenceError("capture title line is malformed or has an ambiguous IPO GMP marker")
        title_issue = title_line[2:].split("IPO GMP", 1)[0]

        if _normalize_issue_name(title_issue) != _normalize_issue_name(company_name):
            raise GmpEvidenceError("capture title line does not identify the evaluated company")

        pct_line_number, pct_quote = evidence_details["market.gmp.pct"]
        pct_line = lines[pct_line_number - 1]
        if market_gmp.get("pct") is None:
            if pct_quote != NOT_QUOTED_YET or pct_line.count(pct_quote) != 1:
                raise GmpEvidenceError("null pct must be tied to the exact 'Not quoted yet' display")
            d3_state = DisplayedGmpState.MISSING.value
        else:
            pct_tokens = [match.group("token") for match in _PERCENT_TOKEN.finditer(pct_line)]
            if len(pct_tokens) != 1 or pct_tokens[0] != pct_quote:
                raise GmpEvidenceError(
                    "pct quote is not the complete, unique signed percentage token on its locator line"
                )
            displayed_state, _displayed_amount = classify_displayed_gmp(pct_quote, unit=PERCENT)
            if displayed_state not in {DisplayedGmpState.ZERO, DisplayedGmpState.AMOUNT}:
                raise GmpEvidenceError("pct quote is not a well-formed displayed percentage")
            pct_number = _decimal_number(market_gmp.get("pct"))
            percentage_match = _PERCENT_AMOUNT.fullmatch(pct_quote)
            if percentage_match is None:
                raise GmpEvidenceError("pct quote has a malformed numeric value")
            try:
                quote_number = Decimal(percentage_match.group("number").replace(",", ""))
            except InvalidOperation as exc:
                raise GmpEvidenceError("pct quote has a malformed numeric value") from exc
            if percentage_match.group("lead") == "-":
                quote_number = -quote_number
            if pct_number is None or quote_number != pct_number:
                raise GmpEvidenceError("market.gmp.pct does not equal the displayed percentage quote")
            d3_state = displayed_state.value

        as_of_line_number, as_of_quote = evidence_details["market.gmp.as_of"]
        as_of_line = lines[as_of_line_number - 1]
        if as_of_line.count(as_of_quote) != 1:
            raise GmpEvidenceError("as_of quote does not occur exactly once on its locator line")
        publisher_instant = _publisher_stamp_instant(as_of_quote)
        input_as_of = explicit_offset_instant(market_gmp.get("as_of"))
        if publisher_instant is None or input_as_of is None:
            raise GmpEvidenceError("as_of quote or input timestamp is not an explicit supported instant")
        if publisher_instant.astimezone(timezone.utc) != input_as_of.astimezone(timezone.utc):
            raise GmpEvidenceError("market.gmp.as_of does not equal the publisher's exact displayed stamp")
        if publisher_instant > capture.retrieved_not_after:
            raise GmpEvidenceError("publisher as_of is later than the capture-window end")

        gmp_block = _record_market_gmp(record)
        snapshot_values = gmp_block.get("values", {}) if isinstance(gmp_block, Mapping) else {}
        if (
            not isinstance(gmp_block, Mapping)
            or gmp_block.get("source_id") != source_id
            or gmp_block.get("as_of") != market_gmp.get("as_of")
            or not isinstance(snapshot_values, Mapping)
            or snapshot_values.get("source_id") != source_id
            or snapshot_values.get("pct") != market_gmp.get("pct")
        ):
            raise GmpEvidenceError("assembled market snapshot changed the linked GMP source or values")
        if market_gmp.get("trend") is not None:
            # A28 extends A18 only for explicit publisher labels, never deltas.
            from .connectors.adapters import _map_gmp_trend_label
            trend_line_number, trend_quote = evidence_details["market.gmp.trend"]
            trend_lines = [line for line in lines if line.startswith("Trend: ")]
            if (
                len(trend_lines) != 1
                or lines[trend_line_number - 1] != f"Trend: {trend_quote}"
                or _map_gmp_trend_label(trend_quote) != market_gmp.get("trend")
                or snapshot_values.get("trend") != market_gmp.get("trend")
            ):
                raise GmpEvidenceError("market.gmp.trend lacks one matching publisher-supplied label")

        evaluation_instant = evaluation_at if isinstance(evaluation_at, datetime) else explicit_offset_instant(evaluation_at)
        if (
            not isinstance(evaluation_instant, datetime)
            or evaluation_instant.tzinfo is None
            or evaluation_instant.utcoffset() is None
        ):
            return _link_result(
                "evaluation timestamp has no explicit timezone offset; capture availability is not established",
                source_id=source_id,
                manifest_uri=manifest_uri,
                manifest_path=manifest_relative,
                artifact_path=artifact_path,
                artifact_id=artifact_id,
                manifest_sha256=manifest_sha256,
                artifact_sha256=artifact_sha256,
                d1_label=d1_label,
                d3_state=d3_state,
                retrieval_window_utc=window_text,
                evidence_refs=available_refs,
                manifest_verified=True,
                artifact_verified=True,
                expected_company_name=company_name,
                expected_pct=market_gmp.get("pct"),
                expected_as_of=market_gmp.get("as_of"),
                expected_trend=market_gmp.get("trend"),
                capture=capture,
                status="NOT_AVAILABLE_BY_CUTOFF",
            )
        if not capture_obtained_by(capture, evaluation_instant):
            return _link_result(
                "the entire capture window does not end at or before the evaluation timestamp",
                source_id=source_id,
                manifest_uri=manifest_uri,
                manifest_path=manifest_relative,
                artifact_path=artifact_path,
                artifact_id=artifact_id,
                manifest_sha256=manifest_sha256,
                artifact_sha256=artifact_sha256,
                d1_label=d1_label,
                d3_state=d3_state,
                retrieval_window_utc=window_text,
                evidence_refs=available_refs,
                manifest_verified=True,
                artifact_verified=True,
                expected_company_name=company_name,
                expected_pct=market_gmp.get("pct"),
                expected_as_of=market_gmp.get("as_of"),
                expected_trend=market_gmp.get("trend"),
                capture=capture,
                status="NOT_AVAILABLE_BY_CUTOFF",
            )
        return _link_result(
            "all link identity, value, integrity, and cutoff checks passed; this is not source qualification",
            source_id=source_id,
            manifest_uri=manifest_uri,
            manifest_path=manifest_relative,
            artifact_path=artifact_path,
            artifact_id=artifact_id,
            manifest_sha256=manifest_sha256,
            artifact_sha256=artifact_sha256,
            d1_label=d1_label,
            d3_state=d3_state,
            retrieval_window_utc=window_text,
            evidence_refs=available_refs,
            manifest_verified=True,
            artifact_verified=True,
            expected_company_name=company_name,
            expected_pct=market_gmp.get("pct"),
            expected_as_of=market_gmp.get("as_of"),
            expected_trend=market_gmp.get("trend"),
            capture=capture,
            status="VERIFIED",
        )
    except (GmpEvidenceError, OSError, TypeError, ValueError, KeyError, IndexError) as exc:
        capture_obj = locals().get("capture")
        return _link_result(
            str(exc) or "link verification failed",
            source_id=source_id,
            manifest_uri=manifest_uri if isinstance(manifest_uri, str) else None,
            manifest_path=locals().get("manifest_relative"),
            artifact_path=locals().get("artifact_path"),
            artifact_id=locals().get("artifact_id"),
            manifest_sha256=locals().get("manifest_sha256"),
            artifact_sha256=locals().get("artifact_sha256"),
            d1_label=locals().get("d1_label", PUBLISHER_REPORTED_RENDERED_CAPTURE),
            d3_state=locals().get("d3_state", DisplayedGmpState.MALFORMED.value),
            retrieval_window_utc=locals().get("window_text"),
            evidence_refs=available_refs,
            manifest_verified=locals().get("manifest_verified", False),
            artifact_verified=locals().get("artifact_verified", False),
            rejected_retrieval_timestamp=rejected_retrieval_timestamp,
            capture=capture_obj if isinstance(capture_obj, RenderedGmpCapture) else None,
        )


def verify_gmp_linkage_projection(
    document: Mapping[str, Any],
    verification: GmpEvidenceLinkVerification,
) -> None:
    """Fail persistence if the final assembled A15 document lost or changed the link.

    This check consumes the already-verified bytes/digests; it does not reread the
    manifest. It runs after the entire A15 object (including diagnostics, digest
    references, and timestamp facts) has been assembled and before persistence.
    """
    link_fields = _link_fields(verification.expected_trend)
    sources = document.get("sources", [])
    evidence = document.get("evidence", [])
    integrity = document.get("integrity", {})
    digests = integrity.get("digests", []) if isinstance(integrity, Mapping) else []
    result = document.get("result", {})
    diagnostics = result.get("diagnostics", []) if isinstance(result, Mapping) else []
    source_rows = [
        item for item in sources
        if isinstance(item, Mapping) and item.get("source_id") == verification.source_id
    ]
    link_diagnostics = [
        item for item in diagnostics
        if isinstance(item, Mapping) and item.get("code") == GMP_LINK_DIAGNOSTIC_CODE
    ]
    if (
        len(link_diagnostics) != 1
        or link_diagnostics[0].get("message") != verification.diagnostic_message
        or link_diagnostics[0].get("evidence_refs") != list(verification.evidence_refs)
    ):
        raise GmpEvidenceError("assembled evaluation document does not preserve the fixed GMP-link diagnostic")

    source_required = (
        verification.status == "VERIFIED"
        or (
            verification.manifest_verified
            and verification.artifact_verified
            and bool(verification.retrieval_window_utc)
        )
    )
    if not source_required:
        if len(source_rows) > 1:
            raise GmpEvidenceError("assembled evaluation document duplicates the attempted GMP source")
        return
    if len(source_rows) != 1:
        raise GmpEvidenceError("assembled evaluation document does not contain exactly one linked source")
    source = source_rows[0]
    if verification.rejected_retrieval_timestamp and any(
        isinstance(item, Mapping) and item.get("kind") == "LOCAL_RETRIEVED_AT"
        for item in source.get("timestamps", [])
    ):
        raise GmpEvidenceError("A15 promoted a rejected retrieval_timestamp to an exact retrieval-time fact")

    if verification.status == "VERIFIED":
        record_section = document.get("record", {})
        if (
            not isinstance(record_section, Mapping)
            or record_section.get("company_name") != verification.expected_company_name
        ):
            raise GmpEvidenceError("assembled A15 record company_name differs from the linked issue")
        expected_ids = set(verification.evidence_refs)
        if expected_ids != {evidence_id for _path, evidence_id in link_fields}:
            raise GmpEvidenceError("verified GMP link lacks required canonical evidence references")
        by_evidence_id = {
            item.get("evidence_id"): item for item in evidence if isinstance(item, Mapping)
        }
        for _path, evidence_id in link_fields:
            item = by_evidence_id.get(evidence_id)
            if (
                not isinstance(item, Mapping)
                or item.get("source_id") != verification.source_id
                or not str(item.get("artifact_ref", "")).startswith("evidence.json#/evidence/evidence/")
            ):
                raise GmpEvidenceError("assembled A15 evidence object is not bound to the verified source")

        field_values = document.get("field_values", [])
        by_field_path = {
            item.get("field_path"): item for item in field_values if isinstance(item, Mapping)
        }
        expected_fields = (
            ("/input/company_name", "EV-company_name", verification.expected_company_name),
            ("/input/market/gmp/pct", "EV-market.gmp.pct", verification.expected_pct),
            ("/input/market/gmp/as_of", "EV-market.gmp.as_of", verification.expected_as_of),
        )
        if verification.expected_trend is not None:
            expected_fields += (("/input/market/gmp/trend", "EV-market.gmp.trend", verification.expected_trend),)
        for field_path, evidence_id, expected_value in expected_fields:
            field_value = by_field_path.get(field_path)
            if not isinstance(field_value, Mapping) or evidence_id not in field_value.get("evidence_refs", []):
                raise GmpEvidenceError("assembled A15 field value lost its canonical GMP evidence reference")
            if expected_value is None:
                reason = field_value.get("reason")
                if (
                    field_value.get("value_state") != "UNKNOWN"
                    or not isinstance(reason, Mapping)
                    or reason.get("code") != "MISSING"
                ):
                    raise GmpEvidenceError("assembled A15 field value does not preserve the linked null as UNKNOWN")
            elif (
                field_value.get("value_state") != "VALUE"
                or type(field_value.get("raw_value")) is not type(expected_value)
                or field_value.get("raw_value") != expected_value
                or type(field_value.get("normalized_value")) is not type(expected_value)
                or field_value.get("normalized_value") != expected_value
            ):
                raise GmpEvidenceError("assembled A15 field value differs from the linked input value")

        expected_digest_values = {
            _stable_link_manifest_digest_id(verification.source_id): verification.manifest_sha256,
            _stable_link_artifact_digest_id(verification.source_id, verification.artifact_id): verification.artifact_sha256,
        }
        by_digest_id = {
            item.get("digest_id"): item for item in digests if isinstance(item, Mapping)
        }
        for digest_id, digest_value in expected_digest_values.items():
            item = by_digest_id.get(digest_id)
            expected_subject = (
                verification.manifest_path
                if digest_id == _stable_link_manifest_digest_id(verification.source_id)
                else verification.artifact_path
            )
            if (
                not isinstance(item, Mapping)
                or item.get("algorithm") != "SHA-256"
                or item.get("digest_value") != (digest_value or "").lower()
                or item.get("subject_kind") != "RAW_ARTIFACT_BYTES"
                or item.get("subject_ref") != expected_subject
                or item.get("origin") != "LOCAL_COMPUTED"
                or item.get("evidence_refs") != sorted(verification.evidence_refs)
            ):
                raise GmpEvidenceError("assembled A15 digest does not match the bytes verified for the link")
        refs = set(source.get("digest_refs", []))
        if not set(expected_digest_values).issubset(refs):
            raise GmpEvidenceError("assembled A15 source lost a verified manifest or artifact digest reference")

    if (
        verification.manifest_verified
        and verification.artifact_verified
        and verification.retrieval_window_utc
    ):
        expected_window = verification.retrieval_window_utc
        timestamps = source.get("timestamps", [])
        window_facts = [
            item for item in timestamps
            if isinstance(item, Mapping)
            and item.get("kind") == "LOCAL_RETRIEVED_AT"
            and item.get("source_text") == expected_window
        ]
        expected_reason = {
            "code": "UNAVAILABLE",
            "message": "exact receipt time not captured; the manifest records only this bracketing window",
        }
        if (
            len(window_facts) != 1
            or window_facts[0].get("state") != "UNKNOWN"
            or window_facts[0].get("reason") != expected_reason
            or window_facts[0].get("evidence_refs") != sorted(verification.evidence_refs)
        ):
            raise GmpEvidenceError("assembled A15 source does not preserve the honest capture-window fact")
        if "normalized_utc" in window_facts[0]:
            raise GmpEvidenceError("assembled A15 capture-window fact invents an exact retrieval timestamp")


__all__ = [
    "A9_MISSING",
    "A9_SOURCE_UNQUALIFIED",
    "GMP_LINK_DIAGNOSTIC_CODE",
    "GMP_LINK_EVIDENCE_FIELDS",
    "NOT_QUOTED_YET",
    "PERCENT",
    "PUBLISHER_REPORTED_RENDERED_CAPTURE",
    "RUPEE",
    "DisplayedGmpState",
    "GmpCaptureAssessment",
    "GmpEvidenceError",
    "GmpEvidenceLinkVerification",
    "RenderedGmpCapture",
    "a9_reason_for",
    "assess_capture",
    "capture_gmp_linkage_context",
    "capture_obtained_by",
    "classify_displayed_gmp",
    "load_rendered_capture",
    "verify_gmp_evidence_link",
    "verify_gmp_linkage_projection",
    "_stable_link_artifact_digest_id",
    "_stable_link_manifest_digest_id",
]
