# Delivery transport — IPO Screening Engine v1.5

This directory exists because **a commit hash is not a usable reference for this
delivery**, and a lesson learned the hard way: the work was built in a session
whose GitHub access was already closed, so its commits were never pushed. A later
verification session, running in a *different* sandbox, found nothing — because a
fresh clone contains only the baseline.

| Where | Has the delivery? |
| --- | --- |
| The originating session's workspace | yes — recovered, see below |
| `origin/main` on GitHub (`01ba66c`) | no: the baseline, unmerged, as required |
| The older implementation branch (`2562749`) | no: not this work |
| Any other session's fresh clone | no — **this is the trap** |

## Structure

| Ref | What it is |
| --- | --- |
| tag `v1.5-delivery` | **The delivery.** The engine, tests, docs and tooling, on top of `01ba66c`; commit and tree hashes are recorded in `carrier/VERIFICATION.txt` |
| branch `arena/01a10abc-ipo-screening-engine` | The delivery **plus one transport commit** carrying this carrier |

The transport commit exists because a git bundle cannot contain the commit that
contains it. The bundle therefore bundles the **tag**, and the tag is the
delivery. Publishing the branch publishes both; publishing the tag alone gives
exactly the delivery.

| Path | What it is |
| --- | --- |
| `make-carrier.sh` | Regenerates the carrier from the local history |
| `verify-delivery.sh` | Verifies a workspace; `ACCEPTED` / `NOT ACCEPTED` / `CANNOT VERIFY` |
| `carrier/ipo-screening-engine-v1.5.bundle` | Thin git bundle (~190 KB); needs only `01ba66c` |
| `carrier/SHA256SUMS` | Checksum of the bundle |
| `carrier/VERIFICATION.txt` | Tip SHA, tree hash, diffstat, and the exact recovery commands |

`carrier/` is **tracked, not ignored**. That is deliberate: a session restore
dropped every git-ignored path — `build/`, `.cache/`, and an earlier ignored copy
of this carrier all disappeared — while source files survived. An ignored carrier
is not a carrier.

Patch series are not committed (they duplicate the tree and are ~4× the bundle);
generate them when needed with `PATCHES=1 ./handoff/delivery/make-carrier.sh`.

## Verify

```bash
./handoff/delivery/verify-delivery.sh
```

Exit `0` = ACCEPTED, `1` = NOT ACCEPTED (something mismatches), `2` = CANNOT
VERIFY (this workspace does not contain the delivery — the wrong-workspace case,
which the script explains rather than misreporting as a failure).

## Materialise

```bash
# A. You have this working tree (this workspace, or a copy including .git).
git push -u origin arena/01a10abc-ipo-screening-engine

# B. You have the bundle. Its prerequisite 01ba66c is origin/main.
git fetch handoff/delivery/carrier/ipo-screening-engine-v1.5.bundle \
    'refs/tags/v1.5-delivery:refs/tags/v1.5-delivery'
git checkout -b arena/<new-branch> v1.5-delivery  # your session's branch
./handoff/delivery/verify-delivery.sh             # expect: ACCEPTED

# C. You have only the plain files (no git objects at all).
git checkout -B arena/01a10abc-ipo-screening-engine 01ba66c
PATCHES=1 ./handoff/delivery/make-carrier.sh     # if the patches are not present
git am handoff/delivery/carrier/patches/*.patch
```

A **new** coding session starts from a fresh clone of GitHub and therefore cannot
see this work either. The publisher must be someone holding the workspace or the
bundle.

## What happened to this delivery, in order

Worth recording, because each step looked like a different failure:

1. **Committed in a closed session.** Remote access was already revoked, so the
   commits never left the sandbox.
2. **A carrier was built — and ignored.** It worked, but being git-ignored it was
   not durable.
3. **A verification ran in another sandbox.** It found no tag, no carrier, no
   `engine/`. It correctly reported NOT ACCEPTED — and correctly refused to
   reimplement anything. The finding was right; the workspace was wrong.
4. **The session's `.git` was replaced** by a fresh shallow clone (`HEAD`
   `7f846dc`). Every original commit object was destroyed.
5. **The working tree survived intact.** Rebuilding a tree from it reproduced
   `5f7a24d04b8576fc64f7f9fbd201d1cfe31f547c` — bit-for-bit the hash recorded
   before the loss. That hash is the proof the content was never damaged, and
   the reason the delivery could be re-established on `01ba66c` under the
   `v1.5-delivery` tag with confidence rather than guesswork.

The lesson encoded above: **track the carrier, and verify the tree hash rather
than the commit hash.** Commit hashes were unrecoverable; the tree hash was not,
and it is what actually describes the content.
