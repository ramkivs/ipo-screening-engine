# A31 — Issue identity binding for closed exchange records

- **Record ID:** A31
- **Status:** **IMPLEMENTED UNDER THE STANDING PA (2026-10-24); SUBMITTED FOR RAMKI'S RATIFICATION**
- **Decision authority:** RAMKI (standing PA for this workstream, 2026-10-24). Implementation performed by the agent within that authority.
- **Decision date:** 2026-10-24 (Asia/Calcutta)
- **Repository:** `ramkivs/ipo-screening-engine`
- **Baseline:** branch `arena/07f3439f-ipo-screening-engine`, from `0cf9d54f96db2d897dcde62ce7b6fc09c7de4983`; `main` untouched at `01ba66c12ca1195fd7acbd287c3e39a019808094`
- **Scope:** how a **closed** exchange listing record may be used to supply issue terms, and the issue-identity model that decides it.

## 1. The problem this resolves

The engine searches the exchange's **live** public-issues listing. Once an issue closes, the exchange moves it to a **historical** listing and the live listing stops carrying the row. For the Paras Healthcare filing the three required pricing terms (`price_band_low`, `price_band_high`, `lot_size`) exist **only** on the closed-issue issue-information page; the filed RHP prints `[●]`. The terms are therefore unresolvable through live discovery, which is a coverage gap and not a defect in the filing.

The prior contract was: live records only (`Status` in `F`/`L`), historical listing never searched. That contract is correct as a default — a closed archive is a list of *past* offerings, and matching one by issuer name would let an older IPO answer for the current one.

## 2. The decision

Closed-issue records become usable **only through an identity-bound path**, never by name match:

1. The closed-issue listing is **off by default**. It is searched only when an operator configures it (`IPO_OFFICIAL_HISTORICAL_LISTINGS`, allow-listed official hosts, HTTPS).
2. A record is eligible only when **all** of the following hold:
   - the served row names this issuer exactly (normalised legal-name equality, as everywhere else);
   - the row states **both** issue dates and they equal the bid window the filing itself establishes (`issue.open_date` / `issue.close_date` in the canonical input) — two offerings by one issuer cannot share a bid window;
   - the row carries the exchange's own **issue number** (`IPONo`) and a well-formed scrip id, so it identifies an *issue*, not merely a company;
   - the row's identifiers are **internally consistent**: a link whose `startdt` contradicts the row's start date, a non-IPO record type, or a missing scrip id is a conflict and the record is withheld;
   - where the caller also supplies an expected issue number or symbol, those must match.
3. **No expected window ⇒ no admission.** Without the filing's own dates every record is withheld as `IDENTITY_UNBOUND`. A closed record is never usable on a name match alone.
4. **Conflicts withhold, they do not arbitrate.** Ambiguous or contradictory records are rejected with a stated reason, which is reported to the operator; no value is chosen, and no default is applied.
5. **Silence here is not absence.** A closed-issue archive cannot contain an issue that is still forthcoming, so a search of it never substantiates `NOT_FOUND`/`UNPUBLISHED`. Such attempts are recorded with classification `historical` and `searched=False` for the purpose of that conclusion.
6. The **live** path is unchanged: same listings, same status filter, same `searched` semantics. No existing behaviour is broadened.

The model lives in `engine/ipo_screening/issue_identity.py` and is issuer-independent: nothing in it names an issuer, a symbol, an issue number or a document.

## 3. Evidence

- Implementation: `issue_identity.py` (identity model + verdicts `BOUND`, `IDENTITY_UNBOUND`, `IDENTITY_INCOMPLETE`, `STALE_OR_DIFFERENT_ISSUE`, `IDENTITY_CONFLICT`); `official_issue_sources.bse_historical_issue_records`; `OfficialDiscoveryProvider.historical_listing_urls` + `_search_historical_listing`; `IssueTermsResolver` forwards `issue_context` to providers that declare it.
- Tests: `tests/test_historical_issue_identity.py` (35 cases) and the closed-archive cases in `tests/test_paras_official_issue_page_terms.py`. They cover the bound record, a previous offering by the same issuer, a same-window record with a different issue number, a missing issue number, a link/row date contradiction, a non-IPO record, a foreign issuer, a similar name, an unreadable price cell, transport failure, source-isolation, cross-issuer leakage, two issue numbers claiming one window, the same issue listed twice, conflict withholding, cap-without-floor, lot-vs-maximum-bid-quantity, and the required-term gate.
- Real evidence: the retained BSE capture (`evidence/non-authoritative/paras-healthcare-issue-terms-20261024/`) supplies the identifiers the tests use, and the tests fail if the capture and the fixture drift apart.

## 4. What this decision deliberately does NOT do

- It does **not** add the historical listing to the default search, and an unconfigured deployment behaves exactly as before.
- It does **not** widen any allow-list. In particular the BSE document archive (`listing.bseindia.com`) remains reachable **only** through issuer-matched discovery; making it legal for operator-configured notice URLs would contradict `tests/test_automatic_official_issue_discovery.py::test_archive_hosts_are_scoped_to_issuer_matched_discovery_not_direct_prospectus_urls`, so that change was **not** made. See §5.
- It does **not** resolve any term for any issuer. No value from the retained capture entered any configuration, canonical record, snapshot or evaluation.
- It does **not** create, update or authorize an evaluation.

## 4a. Runtime wiring (added 2026-10-24)

The rule is only useful if the application actually reaches it, so the chain is asserted end to end in `tests/test_historical_listing_wiring.py`:

* `create_app()` → `PresentationService` → `build_resolver_from_env()` → `OfficialDiscoveryProvider(historical_listing_urls=…)` is the real construction path (`presentation/service.py:161-166`), and the test builds the service the same way.
* The resolver forwards the canonical `issue` mapping to providers that declare it, so the expected window reaches the archive search. Proven by ingesting the retained RHP through `ingest_document` and recording what the resolver received: `2026-10-21`..`2026-10-23`, exactly the three pricing fields missing, then `AWAITING_ISSUE_TERMS` with no evaluation written.
* Misconfiguration now surfaces as a configuration-diagnostic provider (variable, entry position, reason — never the value) rather than as a per-ingestion note that looks identical to a network outage.
* The archive search itself remains opt-in and off by default: an unconfigured deployment behaves exactly as it did before this record.

Operational runbook for a host with official-source egress: report §18.4 (commands, success criteria, failure signatures).

## 5. Open item submitted to RAMKI (not decided here)

**Source allow-list for operator-configured notice URLs.** The BSE price-band advertisement for this issue lives on `listing.bseindia.com`, which is in `DISCOVERY_HOSTS` but not in `OFFICIAL_HOSTS`. A configured `IPO_PRICE_BAND_NOTICE_URLS` entry pointing at that document is therefore **REJECTED** before retrieval ("host is not an HTTPS official source host"). This was found by tracing the configured-URL path end to end, not by inference.

Two ways to close it, and both are RAMKI's call, not the agent's:

- **Preferred, no policy change:** let discovery follow the exchange's own link from the issuer-matched issue page. This required only a *document-naming* recognition — BSE publishes the advertisement as `PBA_<yyyymmdd…>.pdf`, which no anchor text necessarily echoes ("Click Here") — and that naming rule **has been implemented** in this pass, still inside the existing allow-list and still subject to issuer matching and class verification after retrieval.
- **Requires a source-policy decision:** admit `listing.bseindia.com` (and/or `nsearchives.nseindia.com`) as a valid host for *configured* notice/Prospectus URLs. That reverses a deliberate scoping with its own test, so it is left undone and recorded here.

## 6. Consequences and constraints

- A closed record can never be the sole basis for a term without the filing's own issue window; issuers whose filings state no dates gain nothing from this path, which is intended (fail-closed).
- Operators gain a configuration knob (`IPO_OFFICIAL_HISTORICAL_LISTINGS`) and a per-attempt record (`classification="historical"`), so a closed-archive search is visible in diagnostics and distinct from a live search.
- The field-level `STALE_OR_DIFFERENT_ISSUE` check in `issue_term_fields.resolve_fields` remains a second, independent line of defence.
- Engine evaluation readiness is unchanged by this record: the required-term gate still decides it.

## 7. Unresolved dependencies

- RAMKI's ratification of this record and of the frozen-core pin (A30 §5.6).
- RAMKI's decision on the configured-URL allow-list (§5) if the discovery-followed route proves insufficient in practice.
- Live resolution for the Paras filing still requires an environment with egress to the official hosts; this sandbox has none.

## 8. Implementation authority

**Granted for this pass** by the standing PA, limited to: the issue-identity model, the opt-in closed-issue search, the configuration knob, the document-naming recognition for exchange advertisement filenames, diagnostics, and tests. **Not granted, and not done:** any change to scoring, criteria, required-term policy, source allow-lists, the live listing set, the RHP placeholder rules, the golden record, or any evaluation.

## 4b. Operator-facing hardening (added 2026-10-24, revision 10)

The rule above is only as usable as the two things an operator does with it: **configure the archive URL** and **ask for the terms**. Both were repaired after the first real operator run.

**The configured URL is normalised before it is validated.** An operator on a Windows host pasted the archive URL out of a rendered document, so what reached the environment variable was a Markdown link with an HTML-escaped ampersand:

```
[https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&amp;Type=P](https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=2&Type=P)
```

The previous build rejected that as *"not an allowed official source host"* — an operator mistake reported as a **source-policy violation**, which is the most misleading diagnostic available because it suggests the source is disallowed when in fact it is permitted. `normalize_configured_url()` now strips Markdown link syntax, enclosing angle brackets and quotes, and unescapes `&amp;`/entities **before** validation, for `IPO_OFFICIAL_HISTORICAL_LISTINGS` and for the `IPO_PRICE_BAND_NOTICE_URLS` / `IPO_PROSPECTUS_URLS` maps. It is deliberately narrow, and the tests pin the narrowness: no scheme is added (`www.bseindia.com/x` stays as written), no host or path is rewritten, and a value that resolves to a genuinely foreign host is still rejected with the same reason. Normalisation is a presentation fix, not a policy relaxation — §4's "does not widen any allow-list" applies unchanged.

**A retrieved page is now described by what it contains, not by the fact that it arrived.** A 14 KB response proves bytes; it does not prove the page carried issue rows. `bse_historical_issue_records(..., diagnostics=…)` reports `issue_rows` / `issuer_rows` / `bound_rows` / `rejections`, and `_search_historical_listing` says which case occurred:

* *"the served HTML carried no issue-information links at all (N bytes, starts b'…'); this is not a usable closed-issue listing and nothing may be concluded from its silence"* — wrong document; the operator should check the URL;
* *"the served page carried N issue row(s) but none for this issuer"* — right document, different answer.

Without the distinction, a shell, an interstitial or an error page produces exactly the silence that §5 says must never be read as absence. This is the same principle applied one layer out.

**The resolution step is a CLI, not a pasted script.** `python engine/tools/ipo_screen.py issue-terms --issuer … --open … --close … [--fields …] [--json]` is read-only: it builds the resolver from the environment, prints per-source `searched` / `failed` / `historical` / `homepage`, every rejection note, and per field the value, verification state, URI, quote and locator. Exit `0` = `RESOLVED`, `1` = not resolved, `2` = usage error. It writes no store, creates no evaluation, and does not touch any durable record. The command and its expected output are in report §19.2; the tests are `tests/test_issue_terms_cli.py`.

**Tests for this section:** `tests/test_issue_terms_cli.py` (19 cases: the paste forms above, the rejection that must survive normalisation, the two diagnostics messages and their counts, exit codes, `--json`, per-source and per-field rendering, and the closed-issue-without-a-window refusal).

**Still unchanged:** the allow-list itself, the default search set, the frozen core, and the gate. `listing.bseindia.com` for *configured* notice URLs remains RAMKI's decision (§5).
