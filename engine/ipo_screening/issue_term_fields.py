"""Field-wise resolution over existing provider candidates, without new authority rules."""
from __future__ import annotations

import copy
import math
from datetime import date
from typing import Any


#: What evidence would satisfy each required/discoverable field.  Descriptive
#: only: it states which authoritative document establishes the field and
#: never widens, narrows or reorders the requirement itself.
_REQUIRED_EVIDENCE = {
    "fresh_issue": "an issuer-matched official RHP, final Prospectus or exchange issue page that states the "
                   "fresh-issue monetary amount explicitly (a placeholder share count does not by itself "
                   "prevent a stated amount being read)",
    "ofs": "an issuer-matched official RHP, final Prospectus or exchange issue page that states the Offer for "
           "Sale amount explicitly, or an explicit NIL for the Offer for Sale; absence is never read as zero",
    "price_band_low": "an official price band notice or offer document stating the floor price",
    "price_band_high": "an official price band notice or offer document stating the cap price",
    "lot_size": "an official price band notice or offer document stating the bid lot / market lot",
    "open_date": "an official document stating the current issue's bid opening date",
    "close_date": "an official document stating the current issue's bid closing date",
}


def resolve_fields(resolver, outcome, candidates, company_name, ipo_id, missing_fields, from_cache, issue_context):
    from .issue_terms import DISCOVERABLE_TERMS, PRICING_TERMS, ProviderReport, _norm_name, _values_valid

    by_field = {name: [] for name in DISCOVERABLE_TERMS}
    payloads = {}
    for candidate in candidates:
        if _norm_name(candidate.result.company_name) != _norm_name(company_name):
            outcome.provider_reports.append(ProviderReport(candidate.provider, "REJECTED", "issuer identity mismatch"))
            continue
        # Different issue windows must not be silently spliced, even for the same issuer.
        mismatched = any(issue_context.get(k) and getattr(candidate.result, k, None)
                         and str(issue_context[k]) != str(getattr(candidate.result, k).value)
                         for k in ("open_date", "close_date"))
        if mismatched:
            outcome.provider_reports.append(ProviderReport(candidate.provider, "REJECTED",
                "STALE_OR_DIFFERENT_ISSUE: explicit issue dates differ from uploaded filing"))
            continue
        payload = copy.deepcopy(candidate.result.to_enrichment_dict(ipo_id=ipo_id))
        sources = payload.get("sources", [])
        if not sources:
            outcome.provider_reports.append(ProviderReport(candidate.provider, "REJECTED", "missing source identity"))
            continue
        src = sources[0]
        src["uri"] = candidate.uri
        src["retrieval_timestamp"] = candidate.retrieved_at
        sid = src.get("source_id")
        payloads[id(candidate)] = payload
        for name in DISCOVERABLE_TERMS:
            amount = name in ("fresh_issue", "ofs")
            obj = payload.get(name + "_amount") if amount else payload.get("price_band", {}).get(name)
            if not isinstance(obj, dict):
                continue
            value = obj.get("value") if amount else obj.get("normalized_value")
            if value is None:
                continue
            valid = True
            normalized = value
            if name in PRICING_TERMS:
                valid = _values_valid({name: value}) is None
            elif amount:
                from .enrichment_engine import EnrichmentEngine
                multiplier = EnrichmentEngine._UNIT_MULTIPLIERS.get(obj.get("unit"))
                valid = (not isinstance(value, bool) and isinstance(value, (int, float))
                         and math.isfinite(value) and value >= 0 and multiplier is not None)
                normalized = value * multiplier if valid else value  # compare amounts in INR
            else:
                try:
                    date.fromisoformat(str(value))
                except ValueError:
                    valid = False
            verified = bool(candidate.verified and sid and src.get("content_hash")
                            and candidate.uri and candidate.retrieved_at
                            and obj.get("verification") == "VERIFIED")
            entry = {"canonical_field": "issue." + name, "ipo_id": ipo_id,
                     "source_type": src.get("source_type"), "content_hash": src.get("content_hash"),
                     "document_class": getattr(candidate.result, "document_class", "PRICE_BAND_NOTICE"),
                     "value": value, "comparison_value": normalized,
                     "raw_value": obj.get("raw_value", value), "raw_text": obj.get("quote"),
                     "normalization_method": "explicit stated unit to INR for comparison" if amount else "canonical parser",
                     "unit": obj.get("unit"), "source_id": sid, "uri": candidate.uri,
                     "provider": candidate.provider, "issuer": candidate.result.company_name,
                     "retrieved_at": candidate.retrieved_at,
                     "source_timestamp": src.get("source_timestamp") or None,
                     "locator": obj.get("locator"), "page": obj.get("page"),
                     "quote": obj.get("quote"), "extraction_method": obj.get("extraction_method"),
                     "confidence": obj.get("confidence", getattr(
                         getattr(candidate.result, name + "_amount" if amount else name, None), "confidence", None)),
                     "validation": "VALID" if valid else "MALFORMED_OR_AMBIGUOUS",
                     "verification": "VERIFIED" if verified else "UNVERIFIED"}
            by_field[name].append((candidate, obj, entry, valid, verified))

    selected = {}
    for name, entries in by_field.items():
        eligible = [e for e in entries if e[3] and e[4]]
        unique = {e[2]["comparison_value"] for e in eligible}
        if len(unique) > 1:
            state = "CONFLICT"
            outcome.conflicts.append(f"issue.{name}: conflicting official values " + str(sorted(unique)))
        elif eligible:
            state = "VERIFIED"
            selected[name] = eligible[0]
        elif any(e[3] for e in entries):
            state = "CANDIDATE_AWAITING_VERIFICATION"
        elif entries:
            state = "MALFORMED_OR_AMBIGUOUS"
        else:
            state = ("MALFORMED_OR_AMBIGUOUS" if any(
                name in getattr(c.result, "metadata", {}).get("issue_term_errors", {}) for c in candidates)
                else "UNRESOLVED_AFTER_DISCOVERY")
        outcome.field_diagnostics[name] = {"state": state, "candidates": [e[2] for e in entries],
            "qualifications": (["Unverified candidate disagrees; not used to override official evidence"]
                if eligible and any(e[3] and not e[4] and e[2]["comparison_value"] not in unique for e in entries) else []),
            "freshness": "No new numeric freshness policy; explicit lifecycle mismatch rejected; publication date may be unavailable"}

    # Cross-field checks must also work when sources supply separate fields.
    values = {name: e[2]["value"] for name, e in selected.items()}
    invalid = _values_valid(values)
    dates_bad = (values.get("open_date") and values.get("close_date")
                 and values["open_date"] > values["close_date"])
    if invalid or dates_bad:
        names = ("open_date", "close_date") if dates_bad else ("price_band_low", "price_band_high")
        for name in names:
            selected.pop(name, None)
            outcome.field_diagnostics[name]["state"] = "MALFORMED_OR_AMBIGUOUS"
        outcome.provider_reports.append(ProviderReport("field-resolver", "REJECTED", invalid or "close_date precedes open_date"))

    # Explain every field that did not resolve.  This is additive reporting:
    # the states above and the required-term contract are unchanged, but an
    # operator can now see *which* qualified sources and document types were
    # inspected, whether the field was absent, a placeholder, unreadable or
    # contradictory, and what evidence would satisfy it -- instead of a bare
    # "unresolved" list.
    for name in DISCOVERABLE_TERMS:
        diag = outcome.field_diagnostics.get(name)
        if diag is None or name in selected:
            continue
        inspected = []
        reasons = set()
        for candidate in candidates:
            if _norm_name(candidate.result.company_name) != _norm_name(company_name):
                continue
            metadata = getattr(candidate.result, "metadata", {}) or {}
            document_class = getattr(candidate.result, "document_class", "PRICE_BAND_NOTICE")
            inspected.append({"provider": candidate.provider, "document_class": document_class,
                              "uri": candidate.uri, "verified": bool(candidate.verified)})
            if name in (metadata.get("issue_term_errors") or {}):
                reasons.add("CONFLICTING_EVIDENCE_IN_DOCUMENT: " + str(metadata["issue_term_errors"][name]))
            for item in metadata.get("issue_term_diagnostics") or []:
                if item.get("field") == name and item.get("code") == "SOURCE_PLACEHOLDER":
                    reasons.add(f"PLACEHOLDER_IN_QUALIFIED_DOCUMENT: page {item.get('page')}")
            for item in metadata.get("issue_term_findings") or []:
                code = str(item.get("code") or "")
                if name in ("price_band_low", "price_band_high") and code == "CONFLICTING_PRICE_BANDS":
                    reasons.add("CONFLICTING_EVIDENCE_IN_DOCUMENT: " + str(item.get("message")))
                if name == "lot_size" and code == "CONFLICTING_LOT_SIZES":
                    reasons.add("CONFLICTING_EVIDENCE_IN_DOCUMENT: " + str(item.get("message")))
                if name in ("open_date", "close_date") and code in (
                        "CONFLICTING_OPEN_DATES", "CONFLICTING_CLOSE_DATES", "INVALID_ISSUE_DATE_ORDER"):
                    reasons.add("CONFLICTING_EVIDENCE_IN_DOCUMENT: " + str(item.get("message")))
            for item in metadata.get("historical_dates_excluded") or []:
                if name in ("open_date", "close_date") and item.get("field") == name:
                    reasons.add(
                        "HISTORICAL_VALUE_EXCLUDED: " + str(item.get("value")) + " on page "
                        + str(item.get("page")) + " (" + str(item.get("reason")) + ")"
                    )
        if not reasons and inspected:
            reasons.add("ABSENT_FROM_INSPECTED_DOCUMENT: the issuer-matched documents examined do not state this field")
        diag["inspected_sources"] = inspected
        diag["why_unresolved"] = sorted(reasons) or ["NO_QUALIFYING_SOURCE: no issuer-matched official source was available"]
        diag["required_evidence"] = _REQUIRED_EVIDENCE.get(name, "an issuer-matched official document that states this field")

    # Build one contract payload with each original field's own source id.
    # No copied fact is attributed to the primary document.
    merged = {"contract_version": "1.0", "ipo_id": ipo_id, "sources": [], "price_band": {}}
    seen = set()
    for name, (candidate, obj, entry, _, _) in selected.items():
        payload = payloads[id(candidate)]
        source = payload["sources"][0]
        if source["source_id"] not in seen:
            merged["sources"].append(source)
            seen.add(source["source_id"])
        if name in ("fresh_issue", "ofs"):
            merged[name + "_amount"] = copy.deepcopy(obj)
        else:
            merged["price_band"][name] = copy.deepcopy(obj)
    outcome.resolved_fields = [f for f in missing_fields if f in selected]
    outcome.unresolved_fields = [f for f in missing_fields if f not in selected]
    if any(e[3] and not e[4] for entries in by_field.values() for e in entries):
        outcome.provider_reports.append(ProviderReport("candidate-evidence", "UNVERIFIED",
            "Retained/platform candidates lack official verification and cannot satisfy readiness"))
    if not selected:
        outcome.status = "CONFLICT" if outcome.conflicts else "UNVERIFIED" if any(by_field.values()) else "UNAVAILABLE"
        return outcome
    primary = next(iter(selected.values()))[0]
    outcome.notice = copy.deepcopy(primary.result)
    for name in PRICING_TERMS + ("open_date", "close_date"):
        setattr(outcome.notice, name, None)
    # Backward-compatible parsed result view; runtime assembly uses merged payload.
    for name, (candidate, _, _, _, _) in selected.items():
        if name in PRICING_TERMS + ("open_date", "close_date"):
            setattr(outcome.notice, name, getattr(candidate.result, name))
    outcome.enrichment_payload = merged
    outcome.source_uri = primary.uri
    outcome.provider = primary.provider
    outcome.retrieved_at = primary.retrieved_at
    outcome.verified = True
    outcome.from_cache = from_cache
    outcome.document_class = getattr(primary.result, "document_class", "PRICE_BAND_NOTICE")
    # RESOLVED remains pricing-stage compatibility; readiness is recomputed after
    # existing OFS derivation/required-field validation at the service gate.
    remaining = [f for f in outcome.unresolved_fields if f != "ofs"]
    outcome.status = "CONFLICT" if outcome.conflicts else "PARTIAL" if remaining else "RESOLVED"
    if (resolver.cache is not None and not from_cache and len(candidates) == 1
            and primary.raw_bytes is not None and outcome.document_class == "PRICE_BAND_NOTICE"):
        resolver.cache.put(ipo_id, primary)
    return outcome
