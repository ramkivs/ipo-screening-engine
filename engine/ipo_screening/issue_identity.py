"""Issue identity — binding an official record to one exact offering.

An exchange listing can name an issuer more than once: a company that
has already been listed, or one with a second public issue in a later
year, appears in the same historical archive as the offering under
examination.  Matching on the company name alone would let an older
offering's price band and lot answer for the current issue, which is
exactly the wrong-evidence failure this module exists to prevent.

The model is deliberately small and issuer-independent.  An identity has
five parts, of which the issue window is mandatory and the rest are used
when both sides declare them:

* ``open_date`` / ``close_date`` -- the bid window.  Two offerings by one
  issuer cannot share a bid window, so an exact window match binds a
  record to that offering.
* ``issue_number`` -- the exchange's own issue number (BSE ``IPONo``).
* ``symbol`` -- the exchange trading symbol.
* ``uri`` -- where the record was read from (context, not identity).

``check_issue_identity`` answers one question -- may this observed
record be treated as *this* issue? -- and returns a state, never a bare
boolean, so the reason survives into the operator diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

#: Binding verdicts.  Only ``BOUND`` permits a record to supply terms.
BOUND = "BOUND"
#: Nothing to bind to: the caller has not established the expected issue.
IDENTITY_UNBOUND = "IDENTITY_UNBOUND"
#: The record does not carry enough identity to be compared.
IDENTITY_INCOMPLETE = "IDENTITY_INCOMPLETE"
#: The record describes a different offering by (possibly) the same issuer.
STALE_OR_DIFFERENT_ISSUE = "STALE_OR_DIFFERENT_ISSUE"
#: The record's own identifiers contradict each other, or contradict an
#: identifier the caller established.
IDENTITY_CONFLICT = "IDENTITY_CONFLICT"


def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@dataclass(frozen=True)
class IssueIdentity:
    """What is known about the offering a record must belong to."""

    open_date: Optional[str] = None
    close_date: Optional[str] = None
    issue_number: Optional[str] = None
    symbol: Optional[str] = None
    uri: Optional[str] = None

    @classmethod
    def from_issue_context(cls, context: Optional[Mapping[str, Any]]) -> "IssueIdentity":
        """Build the expected identity from a canonical ``issue`` mapping.

        Only fields the filing itself establishes are used.  A date may
        arrive as a ``date``/``datetime`` or an ISO string; anything else
        is ignored rather than guessed at, so a malformed value can only
        make the identity weaker, never make an unrelated record match.
        """
        if not isinstance(context, Mapping):
            return cls()
        return cls(
            open_date=_clean(context.get("open_date")),
            close_date=_clean(context.get("close_date")),
            issue_number=_clean(context.get("issue_number")),
            symbol=_clean(context.get("symbol")),
        )

    def with_uri(self, uri: Optional[str]) -> "IssueIdentity":
        return IssueIdentity(self.open_date, self.close_date, self.issue_number,
                             self.symbol, uri)

    @property
    def binds_window(self) -> bool:
        """True when the expected identity can bind an offering at all."""
        return bool(self.open_date and self.close_date)


@dataclass
class IdentityCheck:
    """The verdict on one observed record, with the reason kept."""

    eligible: bool
    state: str
    reasons: list[str] = field(default_factory=list)
    expected: Optional[IssueIdentity] = None
    observed: Optional[IssueIdentity] = None

    def as_dict(self) -> dict:
        return {
            "eligible": self.eligible,
            "state": self.state,
            "reasons": list(self.reasons),
            "expected": _identity_dict(self.expected),
            "observed": _identity_dict(self.observed),
        }


def _identity_dict(identity: Optional[IssueIdentity]) -> Optional[dict]:
    if identity is None:
        return None
    return {
        "open_date": identity.open_date,
        "close_date": identity.close_date,
        "issue_number": identity.issue_number,
        "symbol": identity.symbol,
        "uri": identity.uri,
    }


def check_issue_identity(
    observed: IssueIdentity,
    expected: Optional[IssueIdentity],
    *,
    conflicts: Optional[list[str]] = None,
) -> IdentityCheck:
    """Decide whether ``observed`` may be treated as ``expected``.

    Fail-closed at every step:

    * no expected window          -> ``IDENTITY_UNBOUND``   (never binds)
    * observed window missing      -> ``IDENTITY_INCOMPLETE``
    * windows differ               -> ``STALE_OR_DIFFERENT_ISSUE``
    * declared identifiers clash   -> ``IDENTITY_CONFLICT``
    * otherwise                    -> ``BOUND``

    ``conflicts`` carries contradictions the caller found *inside* the
    record (for example a listing row whose date contradicts the issue
    page it links to).  A record that contradicts itself is never bound,
    however well its dates happen to line up with the expectation.
    """
    if conflicts:
        return IdentityCheck(False, IDENTITY_CONFLICT, list(conflicts), expected, observed)
    if expected is None or not expected.binds_window:
        return IdentityCheck(
            False, IDENTITY_UNBOUND,
            ["no expected issue window is established for this filing; an exchange record "
             "cannot be bound to the offering without one"],
            expected, observed,
        )
    if not (observed.open_date and observed.close_date):
        return IdentityCheck(
            False, IDENTITY_INCOMPLETE,
            ["the record does not state both issue dates, so its offering cannot be identified"],
            expected, observed,
        )
    if (observed.open_date, observed.close_date) != (expected.open_date, expected.close_date):
        return IdentityCheck(
            False, STALE_OR_DIFFERENT_ISSUE,
            [f"record issue window {observed.open_date}..{observed.close_date} differs from "
             f"the expected {expected.open_date}..{expected.close_date}"],
            expected, observed,
        )
    reasons: list[str] = []
    if expected.issue_number and observed.issue_number != expected.issue_number:
        reasons.append(f"issue number {observed.issue_number!r} differs from the expected "
                       f"{expected.issue_number!r}")
    if expected.symbol and observed.symbol != expected.symbol:
        reasons.append(f"symbol {observed.symbol!r} differs from the expected {expected.symbol!r}")
    if reasons:
        return IdentityCheck(False, IDENTITY_CONFLICT, reasons, expected, observed)
    return IdentityCheck(
        True, BOUND,
        [f"issue window {observed.open_date}..{observed.close_date} matches the expected offering"
         + (f"; issue number {observed.issue_number}" if observed.issue_number else "")
         + (f"; symbol {observed.symbol}" if observed.symbol else "")],
        expected, observed,
    )
