#!/usr/bin/env bash
# Rebuild the delivery commit, its tag, the carrier and the transport commit.
#
#   ./handoff/delivery/rebuild.sh
#
# Run this after changing any delivery file. It exists because the same
# build was previously done by hand four times and went wrong three times, each
# time differently:
#
#   * a stale carrier/ was committed INTO the delivery, so the delivery's own
#     verification record named a tree it did not have;
#   * `git rm -r --cached A B` where B was not in the index failed atomically and
#     removed NEITHER, with the error hidden behind `2>/dev/null || true`.
#
# So this script removes paths ONE AT A TIME and asserts the result before
# committing. A wrong delivery should be impossible to produce, not merely
# unlikely.
#
# Structure it produces:
#
#   baseline 01ba66c
#     └── v1.5-delivery            the delivery: source, tests, docs, tooling
#           └── <branch> tip       transport: the generated bundle and nothing else
#
# carrier/ and download/ are excluded from the delivery because both are
# generated: the bundle cannot contain the commit that contains it, and a copy
# of it is not source.

set -euo pipefail

BASELINE="${BASELINE:-01ba66c12ca1195fd7acbd287c3e39a019808094}"
TAG="v1.5-delivery"
BRANCH="refs/heads/arena/01a10abc-ipo-screening-engine"
DELIVERY_MSG="${DELIVERY_MSG:-Implement IPO Screening Engine v1.5}"
TRANSPORT_MSG="${TRANSPORT_MSG:-Carry the portable bundle}"
EXCLUDE_MSGS="${EXCLUDE_MSGS:-0}"

cd "$(git rev-parse --show-toplevel)"

die() { printf 'rebuild: %s\n' "$1" >&2; exit 1; }
note() { printf '  %s\n' "$1"; }

[ -z "$(git status --porcelain --untracked-files=no)" ] || {
    echo "rebuild: tracked files have uncommitted changes; commit or stash them first." >&2
    echo "         (they would otherwise be swept into the delivery commit)" >&2
    git status --short --untracked-files=no >&2
    exit 1
}

git cat-file -e "$BASELINE^{commit}" 2>/dev/null || die "baseline $BASELINE is not present"

IDX="$(mktemp)"
trap 'rm -f "$IDX"' EXIT

# ---------------------------------------------------------------------------
# 1. The delivery tree: HEAD minus generated paths
# ---------------------------------------------------------------------------
git read-tree "$(git rev-parse HEAD)" >/dev/null   # populates GIT_INDEX_FILE=$IDX below
export GIT_INDEX_FILE="$IDX"
git read-tree "$(git rev-parse HEAD)"

# Remove one at a time. --ignore-unmatch only where absence is legitimate.
git rm -r -q --cached --ignore-unmatch handoff/delivery/download
git update-index --force-remove handoff/delivery/MANIFEST.sha256 2>/dev/null || true
if GIT_INDEX_FILE="$IDX" git ls-files --error-unmatch handoff/delivery/carrier >/dev/null 2>&1; then
    GIT_INDEX_FILE="$IDX" git rm -r -q --cached handoff/delivery/carrier
fi

CARRIER_LEFT="$(GIT_INDEX_FILE="$IDX" git ls-files handoff/delivery/carrier | wc -l)"
[ "$CARRIER_LEFT" -eq 0 ] || die "carrier/ is still staged ($CARRIER_LEFT files); refusing to build a delivery containing generated output"

TREE_PROVISIONAL="$(git write-tree)"
PROVISIONAL="$(git commit-tree "$TREE_PROVISIONAL" -p "$BASELINE" -m "provisional")"
note "delivery tree (pre-manifest): $TREE_PROVISIONAL"

# Check out the provisional delivery so that the manifest describes committed
# contents, and so that carrier/ leaves the working tree.
unset GIT_INDEX_FILE
git checkout -q -f "$PROVISIONAL"
[ ! -d handoff/delivery/carrier ] || die "carrier/ survived the checkout; the delivery tree is wrong"

# ---------------------------------------------------------------------------
# 2. The manifest, then the real delivery commit
# ---------------------------------------------------------------------------
./handoff/delivery/make-manifest.sh

grep -q 'MANIFEST.sha256' handoff/delivery/MANIFEST.sha256 && \
    die "the manifest lists itself; it can never verify"
grep -qE '^[0-9a-f]+  handoff/delivery/(carrier|download)/' handoff/delivery/MANIFEST.sha256 && \
    die "the manifest lists generated paths"

MANIFEST_COUNT="$(wc -l < handoff/delivery/MANIFEST.sha256)"
[ "$MANIFEST_COUNT" -gt 0 ] || die "the manifest is empty"

git add -A
TREE_FINAL="$(git write-tree)"
[ "$(git ls-tree -r --name-only "$TREE_FINAL" | grep -c 'handoff/delivery/carrier/' || true)" -eq 0 ] || \
    die "carrier/ reached the delivery tree"

# The message deliberately names no tree or commit hash: this script is part of
# the tree it describes, so writing a hash into it would change that hash.
cat > /tmp/rebuild-delivery-msg.$$ <<'EOM'
Implement IPO Screening Engine v1.5

Adds the v1.5 engine, executable policy, input contract, golden regression
fixtures, documentation, tests and the CLI, on top of the baseline.

- engine/ipo_screening: 17 modules. Tri-state semantics (VALUE / UNKNOWN /
  NOT_APPLICABLE), Kleene-logic knockouts, a deterministic scorer, schema and
  semantic hard gates, sector and structure overlays, immutable evaluation
  records with hashed artifacts, and the 14-sheet Excel projection.
- config/ipo-config.v1.5.0.json: 6 modules, 30 criteria, 7 penalty rules,
  4 sector overlays, 1 structure overlay, 6 knockouts, 10 validated
  profile x structure plans.
- schema/ipo-input.v1.5.schema.json: draft 2020-12 input contract.
- engine/tools/ipo_screen.py: run / replay / verify / project / check-config.
- fixtures/vishal_nirmiti: golden case (Vishal Nirmiti Limited) frozen at result
  hash e84f8bc0..., plus its five expected-output files.
- handoff/delivery: carrier tooling, the integrity manifest and the handoff
  prompt. The bundle itself rides one transport commit on top, because a git
  bundle cannot contain the commit that contains it.
- tests: 238 passing.

Golden result: final 35.0 of 100 (base 38.0, penalties -3.0), range 25.0-62.0,
verdict INSUFFICIENT_DATA, confidence Low (73/100 evaluable points), knockouts
K1/K5/K6 UNVERIFIED and K2/K3/K4 CLEAR.

Not merged to main. No production deployment.
EOM
DELIVERY="$(git commit-tree "$TREE_FINAL" -p "$BASELINE" -F /tmp/rebuild-delivery-msg.$$)"
rm -f /tmp/rebuild-delivery-msg.$$
git update-ref "refs/tags/$TAG" "$DELIVERY"
git checkout -q -f "$DELIVERY"
note "delivery commit: $DELIVERY"
note "delivery tree:   $TREE_FINAL"

sha256sum -c handoff/delivery/MANIFEST.sha256 > /dev/null || die "the manifest does not verify against the committed tree"
note "manifest verifies: $MANIFEST_COUNT files"

# ---------------------------------------------------------------------------
# 3. The carrier, then the transport commit
# ---------------------------------------------------------------------------
./handoff/delivery/make-carrier.sh > /dev/null
git add -A

# The transport commit must contain the carrier and nothing else.
CHANGED="$(git diff --cached --name-only | grep -vE '^handoff/delivery/carrier/' || true)"
[ -z "$CHANGED" ] || {
    echo "rebuild: the transport commit would also contain:" >&2
    printf '%s\n' "$CHANGED" >&2
    die "carrier-only transport commits keep the delivery the single source of truth"
}

TRANSPORT="$(git commit-tree "$(git write-tree)" -p "$DELIVERY" -m "$TRANSPORT_MSG")"
git update-ref "$BRANCH" "$TRANSPORT"
git symbolic-ref HEAD "$BRANCH"
git reset -q --hard "$TRANSPORT"

note "transport commit: $TRANSPORT  (carrier only)"
echo
echo "delivery tag : $TAG -> $DELIVERY"
echo "delivery tree: $TREE_FINAL"
echo "branch tip   : $TRANSPORT"
echo
echo "Next: re-stage the downloads and verify."
echo "  ./handoff/delivery/stage-downloads.sh"
echo "  ./handoff/delivery/verify-delivery.sh"
