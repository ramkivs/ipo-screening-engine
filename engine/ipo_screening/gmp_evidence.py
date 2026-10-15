"""Approved GMP source-policy decisions D1-D3 as executable, non-qualifying checks.

Decision record: ``docs/investigation/A9-GMP-SOURCE-POLICY-SELECTION-2026-10-15.md`` §6.

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

Nothing here qualifies a source. Passing D1-D3 makes a capture eligible for
cutoff consideration only, subject to every other qualification requirement.
The A9 Final gate is unchanged and still withholds ``FINAL`` for every GMP
observation. No approved contract links an evaluation's GMP value to a retained
capture, so the gate cannot establish D1 or D2 when an evaluation runs. Generic
v1.5 ``_sources``/``_evidence`` fields could carry such a reference, but its
meaning and verification are an unapproved proposal (decision record §7, L1-L4).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from .gmp_policy import explicit_offset_instant
from .strict_json import loads_strict

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


def parse_manifest_bytes(manifest_path: Union[str, Path], raw: bytes) -> Dict[str, Any]:
    """Parse one capture manifest from the exact bytes that were hashed.

    Duplicate JSON keys are rejected here, before any window, hash or cutoff
    decision, because a repeated ``retrievalWindowUtc`` or ``sha256`` would
    otherwise be collapsed to its last value without any error.
    """
    path = Path(manifest_path)
    try:
        manifest = loads_strict(raw)
    except ValueError as exc:
        raise GmpEvidenceError(f"manifest {path.name} is not a strict JSON object: {exc}") from exc
    if not isinstance(manifest, dict):
        raise GmpEvidenceError(f"manifest {path.name} is not a JSON object")
    method = manifest.get("captureMethod")
    if not isinstance(method, Mapping) or method.get("rawProviderResponseBytesCaptured") is not False:
        raise GmpEvidenceError(
            "D1 covers only a retained rendered-text capture, and this manifest does not "
            "declare one (captureMethod.rawProviderResponseBytesCaptured must be false)"
        )
    return manifest


def load_rendered_capture(manifest_path: Union[str, Path], artifact_id: str) -> RenderedGmpCapture:
    """D1: read one declared artifact from a capture manifest and verify its hash.

    The manifest is read once; its bytes are parsed strictly (duplicate keys are
    rejected). See :func:`load_rendered_capture_from_manifest` for the rules.
    """
    path = Path(manifest_path)
    manifest = parse_manifest_bytes(path, path.read_bytes())
    return load_rendered_capture_from_manifest(path, manifest, artifact_id)


def load_rendered_capture_from_manifest(
    manifest_path: Union[str, Path], manifest: Mapping[str, Any], artifact_id: str
) -> RenderedGmpCapture:
    """D1 for an already-parsed manifest (the caller parsed the hashed bytes).

    The caller must have parsed the manifest with :func:`parse_manifest_bytes`.

    Raises :class:`GmpEvidenceError` unless the manifest declares a rendered-text
    capture (``captureMethod.rawProviderResponseBytesCaptured`` is ``false``) and
    the artifact declares a file inside the manifest's directory, a byte count
    and a SHA-256. An artifact id declared more than once is ambiguous and is
    rejected. A missing or altered file is reported, not raised:
    ``integrity_verified`` is ``False``. Retrieval-window bounds without an
    explicit UTC offset, or an inverted window, establish no retrieval window.
    """
    path = Path(manifest_path)
    entries = [
        item
        for item in (manifest.get("artifacts") or [])
        if isinstance(item, Mapping) and item.get("id") == artifact_id
    ]
    if not entries:
        raise GmpEvidenceError(f"artifact {artifact_id!r} is not declared in {path.name}")
    if len(entries) > 1:
        # Two declarations would let one reference resolve to either file.
        raise GmpEvidenceError(f"artifact {artifact_id!r} is declared more than once in {path.name}")
    entry = entries[0]

    file_name = entry.get("file")
    declared = entry.get("sha256")
    size = entry.get("bytes")
    if (
        not isinstance(file_name, str)
        or not file_name
        or not isinstance(declared, str)
        or not _SHA256_HEX.match(declared)
        or not isinstance(size, int)
        or isinstance(size, bool)
        or size < 0
    ):
        raise GmpEvidenceError(
            f"artifact {artifact_id!r} does not declare a retained file, byte count and SHA-256"
        )
    root = path.parent.resolve()
    artifact = (root / file_name).resolve()
    if root not in artifact.parents:
        raise GmpEvidenceError(f"artifact {artifact_id!r} lies outside the manifest's directory")

    data = artifact.read_bytes() if artifact.is_file() else None
    computed = hashlib.sha256(data).hexdigest().upper() if data is not None else None
    verified = data is not None and len(data) == size and computed == declared.upper()
    text: Optional[str] = None
    if verified and data is not None:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None

    window = entry.get("retrievalWindowUtc")
    window = window if isinstance(window, Mapping) else {}
    not_before = explicit_offset_instant(window.get("notBefore"))
    not_after = explicit_offset_instant(window.get("notAfter"))
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


__all__ = [
    "A9_MISSING",
    "A9_SOURCE_UNQUALIFIED",
    "NOT_QUOTED_YET",
    "PERCENT",
    "PUBLISHER_REPORTED_RENDERED_CAPTURE",
    "RUPEE",
    "DisplayedGmpState",
    "GmpCaptureAssessment",
    "GmpEvidenceError",
    "RenderedGmpCapture",
    "a9_reason_for",
    "assess_capture",
    "capture_obtained_by",
    "classify_displayed_gmp",
    "load_rendered_capture",
]
