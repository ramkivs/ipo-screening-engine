# Targeted public-page follow-up — 2026-10-22

**Non-authoritative investigation evidence. All three publishers remain NOT
QUALIFIED. This is not an A28.1 binding, qualification hash, accepted evaluation
or source approval.** Model A remains named publisher-reported, not dealer-verified.

See the [current inventory/addendum](../../../docs/investigation/A9-EVIDENCE-TO-ACCEPTANCE-INVENTORY-2026-10-22.md#targeted-acquisition-continuation).
This package supplements, and never rewrites, the October15 packages.

## Actual acquisition and representation

Only previously documented public routes were requested using the existing
`functions.fetch_page` tool: ML Tonbo and About, IG Tonbo chunks0/1/2, PD Tonbo.
No archive/API discovery, direct publisher curl, new proxy/access method,
publisher contact or PD retry occurred. Available rendered-page access is NOT
an available immutable history/archive endpoint. Tool success is not proof of
HTTP status, publisher authenticity, cache freshness or qualification.

| Local artifact | URL / tool chunk | Tool result | Retained representation |
|---|---|---|---|
| ML-T22 | `https://marketliveipogmp.com/ipo/tonbo-imaging-india`,0/1 | ₹512/+73.1%,21Oct9:37pm IST | Full rendered-content transcription |
| IG-T22-0 | `https://www.investorgain.com/gmp/tonbo-imaging-india-ipo/2369/`,0/3 | ₹445,76 displayed intraday records | Labeled discontinuous excerpts, including COMPLETE daily/intraday tables and conflicting trend labels |
| PD-T22 | `https://www.papsdigital.com/ipo-gmp/tonbo-imaging-india`,0/1 | Temporarily unavailable | Full rendered outage message; NO GMP observation |
| IG-T22-1 | same IG URL,1/3 | FAQ/affiliation, same undefined source clock | Contiguous beginning through FAQ12; comments omitted |
| ML-A22 | `https://marketliveipogmp.com/about`,0/1 | Same methodology/correction claims; new sync/contact address | Full rendered-content transcription |

IG chunk2/3 (index2) was read once to complete inspection. Only comments/footer
were returned; not retained, no invented digest. No comment is publisher evidence.
No linked dashboard/performance/discussion URL was followed merely because it
appears in the page.

These are manually transcribed tool-rendered Markdown contents/excerpts,
**not original provider response bytes**. IG excerpt editorial headings explicitly
identify omissions; no redactions are applied to retained excerpts. Trailing
newlines were added locally. Hashes cover exact retained local bytes including
those additions. No machine comparison against original tool strings is possible.
No HTTP headers, original receipt time, cache status, ETag, stable publisher
observation/version ID or digital source signature was returned/preserved.
Local artifact names are capture IDs, not publisher version IDs. D1 permits
rendered captures; native bytes are not reinstated as a qualification prerequisite.

## Honest time bounds

- First group (ML-T22/IG-T22-0/PD-T22): **17:42:32.252218–17:43:12.825118Z**,
  October22. The lower bound is `.git/FETCH_HEAD` mtime written by this pass's
  fetch, before the tool calls; upper bound is a sandbox UTC read after all three
  completed. This is a deliberately coarse shared bound, NOT an exact tool
  start or receipt, nor three independently clocked windows.
- Second group (IG chunks1/2 and ML-A22): **17:43:12.830244–17:43:35.200412Z**,
  sandbox UTC reads before/after the three parallel tool calls.
- No new independent clock synchronization test was made. Actual publisher
  generation/cache time is unknown. For D2 use each required artifact's window
  end, or the latest end when referring to multiple chunks; never backdate
  availability to displayed source time. Separate chunks are not asserted to be
  one atomic HTTP response.

ML's explicit IST source timestamp normalizes to **2026-10-21T16:07:00Z**;
inclusive A17 expiry is **2026-10-22T16:07:00Z**, before even the conservative
capture lower bound. It cannot support an eligible evaluation cutoff using this
capture. IG timestamps still lack source timezone/event-role definitions; no
implicit IST conversion is made. PD has no observation timestamp in this response.

## New comparison findings (derived, not publisher statements)

- IG: all prior41 intraday rows match the new view's rows36–76 in GMP, raw
  displayed time and trend. There are35 newly displayed rows; ordinal1 now names
  a different displayed record. No common-row same-stamp change/deletion was
  observed. This is not proof that corrections/withdrawals never occurred between
  captures, nor independent corroboration or an immutable revision log.
- IG's prior October15 daily row was17:37/₹495; current October15 daily row is
 23:37/₹500. These are DIFFERENT displayed timestamps, not a proven same-stamp
  correction. Current headline/narrative says upward today while daily/model/FAQ
  says Volatile. No precedence or attributable reconciliation is supplied.
- ML: new current value/time is not byte-identical to October15. Different
  values at different timestamps establish a changed current display, NOT
  before/after versions of one observation. About wording is unchanged apart
  from sync date/contact address (no address contacted). Chart ranges/delta
  still do not expose historical reading/version records.
- PD: no source or independence evidence obtained from an outage. Existing
  declared IG-relay classification remains; outage is not proof of withdrawal.

`capture-manifest.json` records URLs, method, bounds, retention scope, unknown
publisher version identity, byte counts and SHA-256 (existing uppercase retained
file convention). Its derivedChecks are local comparisons, not source attestations.

## Reproduce the new-material checks only

Run from repository root (standard Python, no engine dependencies):

```sh
python - <<'PY'
from pathlib import Path
import json, hashlib, re
p = Path('evidence/gmp-observations/targeted-followup-20261022')
m = json.loads((p / 'capture-manifest.json').read_text())
assert len(m['artifacts']) == 5
for a in m['artifacts']:
    b = (p / a['file']).read_bytes()
    assert len(b) == a['bytes']
    assert hashlib.sha256(b).hexdigest().upper() == a['sha256']
def rows(text):
    return [x[1:] for x in re.findall(
        r'^\| (\d+) \| (.*?) \| (.*?) \| (.*?) \|$', text, re.M)]
old = Path('evidence/gmp-observations/investorgain-tonbo-20261015/source-captures/investorgain-gmp-tonbo-2369-chunk-0.md')
a = rows(old.read_text()); b = rows((p / 'source-captures/ig-chunk0-excerpts.md').read_text())
assert len(a) == 41 and len(b) == 76 and a == b[35:]
about = Path('evidence/gmp-observations/marketliveipogmp-tonbo-20261015/source-captures/marketliveipogmp-about-chunk-0.md')
def comparable(text):
    return '\n'.join(x for x in text.strip().splitlines() if not x.startswith('Last data sync '))
assert comparable(about.read_text()).replace('hello@marketliveipogmp.com', 'marketliveipogmp@gmail.com') == comparable((p / 'source-captures/ml-about.md').read_text())
print('PASS: five new retained files; IG41 shared/35 added rows; ML documented display changes')
PY
```

This does not rerun the completed20-file audit/96-test suite or grant authority.
