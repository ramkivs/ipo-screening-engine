# Prompt for the next coding session

Copy the block below to start a new session. It exists because a new session
boots from a **fresh clone of GitHub**, which contains only the baseline — the
delivery was never pushed, so it cannot be discovered by looking. The first
instruction is therefore to establish where the delivery is, and to stop and ask
rather than rebuild anything.

> **Why this file contains no commit or tree hashes.** It ships inside the
> delivery, and writing a hash into a file changes that hash, so any value here
> would be stale the moment it was written. The authoritative identity lives in
> `handoff/delivery/carrier/VERIFICATION.txt` (generated *after* the commit
> exists) and in `SHA256SUMS` next to the bundle. Read them; do not trust a
> prompt.

---

You are completing the delivery of the **IPO Screening Engine v1.5** for
repository `ramkivs/ipo-screening-engine`. The implementation is **already
complete, committed and green**. Your job is transport and publication, not
engineering. Do not reimplement anything.

## Known facts

| Item | Value |
| --- | --- |
| Baseline | `01ba66c12ca1195fd7acbd287c3e39a019808094` (= `main`, unmodified) |
| Delivery tag | `v1.5-delivery` — resolve it with `git rev-parse`, do not assume a value |
| Commit and tree hashes | `handoff/delivery/carrier/VERIFICATION.txt`, fields `tip:` and `tree:` |
| Branch to publish from | create your own from the tag; Arena pins each session to its own branch |
| Tests | 238 passing |
| Golden result hash | `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` |
| Integrity record | `handoff/delivery/SHA256SUMS` (for the bundle) and `handoff/delivery/MANIFEST.sha256` (for every delivery file) |

## Step 1 — Establish whether the delivery is present

```bash
git rev-parse -q --verify v1.5-delivery^{commit} && echo "TAG PRESENT" || echo "TAG ABSENT"
ls engine/ipo_screening tests/ 2>/dev/null | head
```

- **Both present** → step 3.
- **Neither present** (this is what a fresh clone looks like) → step 2.
- **Files present but no tag** → the content survived but the git history did
  not. Do **not** guess a commit. Run `./handoff/delivery/verify-delivery.sh`:
  it compares the tree against the manifest and the behavioural checks, rather
  than assuming. If it reports NOT ACCEPTED, report that and stop.

## Step 2 — If the delivery is absent, STOP and ask

Do not synthesise, stub or partially reimplement the engine. Report that the
workspace contains only the baseline and ask the user to do one of:

```bash
# A. Attach the bundle to this session, then confirm it before using it:
sha256sum ipo-screening-engine-v1.5.bundle   # must match the sha256 on the download page
git fetch ipo-screening-engine-v1.5.bundle \
    'refs/tags/v1.5-delivery:refs/tags/v1.5-delivery'
git checkout -b arena-ipo-v1.5-publish v1.5-delivery

# B. Or push from the machine that holds the working tree, then clone normally.
```

The bundle requires `01ba66c`, which is already `origin/main`; that is why it is
only about 200 KB.

## Step 3 — Verify (never skip)

```bash
python3 -m pip install --break-system-packages jsonschema openpyxl pytest   # not persisted between sessions
./handoff/delivery/verify-delivery.sh
```

Expect `RESULT: ACCEPTED`. Exit codes: `0` accepted, `1` present but wrong,
`2` **cannot verify — this workspace has no delivery** (a property of the
workspace, not a defect; go back to step 2). The script also checks
`handoff/delivery/MANIFEST.sha256`, which hash-verifies every delivery file
without needing any external record, and it prints the resolved commit and tree.

## Step 4 — Publish

Arena pins each session to its own branch; push there and open the PR from it.

```bash
git push -u origin arena-ipo-v1.5-publish
gh pr create --base main --title "IPO Screening Engine v1.5" --body-file handoff/delivery/README.md
```

Then confirm the remote cannot lie about it:

```bash
git ls-remote origin | grep -E "v1.5-delivery|arena-ipo-v1.5-publish"
```

**Do not merge the pull request, and do not create any production deployment.**

## Step 5 — Report

State: the verified tree hash, the test count, the golden result hash, the
branch as pushed, and the PR URL. If any check failed, say so plainly and stop.

## Hard constraints

- **Never merge to `main`.** It must stay at `01ba66c`.
- **No production deployment.**
- **Do not edit `config/ipo-config.v1.5.0.json`.** Any change alters
  `config_hash` and invalidates every stored result hash and the golden fixtures.
- **Do not regenerate `fixtures/vishal_nirmiti/expected_*.json`** to make a test
  pass. If a test fails, find out why.
- **Never `git reset --hard`, `git clean`, or delete files** to tidy up.
  Untracked and ignored files have already been lost twice that way.
- **Do not commit generated output into the delivery commit.** `carrier/` and
  `download/` are transport-only; `./handoff/delivery/rebuild.sh` enforces this
  and asserts the result. Use it if you must revise the delivery, and never
  hand-assemble the delivery tree.
- Per Spec §21, if something is genuinely ambiguous, **stop and ask** rather
  than inventing policy.

## Policy decisions already settled — do not re-litigate

- **GCP `[●]` is strictly `UNKNOWN`.** The 25% SEBI ICDR ceiling is an upper
  regulatory bound, never substituted for the actual amount. The legacy ₹3,625
  lakh figure must not override the source disclosure.
- **The combined `epc_real_estate` overlay is retained** for v1.5.

## Open items requiring the user, not code

- **Sign-off on the reference fixture** that records the GCP ceiling as an
  amount; the engine follows the specification and therefore rejects it.
- **Whether EPC and real estate should be separate overlays** (a policy call).
- **Shallow coverage**: `sector_ipo_relative` has no fixture with a populated
  `recent_sector_ipos`; the sector overlays are exercised on synthetic inputs
  rather than a real bank filing; no automated extraction exists.

Details in `docs/FINAL_REPORT.md` (section H) and
`docs/TRACEABILITY_MATRIX.md`.
