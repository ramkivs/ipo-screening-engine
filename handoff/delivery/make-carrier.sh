#!/usr/bin/env bash
# Generate the portable delivery carrier for IPO Screening Engine v1.5.
#
# Why this exists: the delivery was built in a session whose GitHub access was
# already closed, so its commits were never pushed and exist only in that
# session's clone. A commit hash cannot be handed to someone else. This script
# turns the local history into files that can be copied, checksummed and
# replayed anywhere.
#
# The generated files are COMMITTED, not ignored. That is deliberate: a fresh
# session's restore dropped every git-ignored path (build/, .cache/ and the
# earlier, ignored copy of this carrier all vanished), so an ignored carrier is
# not a carrier. Everything here is tracked so it survives with the tree.
#
#   ./handoff/delivery/make-carrier.sh              # bundle the v1.5-delivery tag
#   ./handoff/delivery/make-carrier.sh some-tag     # a different tip
#   PATCHES=1 ./handoff/delivery/make-carrier.sh    # also emit git-am patch series
#
# Requires the baseline commit (default 01ba66c) to be present locally.

set -euo pipefail

BASELINE="${BASELINE:-01ba66c12ca1195fd7acbd287c3e39a019808094}"
TIP="${1:-v1.5-delivery}"
EMIT_PATCHES="${PATCHES:-0}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
OUT="handoff/delivery/carrier"

git cat-file -e "$BASELINE^{commit}" 2>/dev/null || {
    echo "error: baseline $BASELINE is not present in this clone." >&2
    echo "       It is origin/main; clone or fetch it first." >&2
    exit 1
}
git rev-parse -q --verify "$TIP^{commit}" >/dev/null || {
    echo "error: tip '$TIP' is not resolvable as a commit in this clone." >&2
    exit 1
}

TIP_SHA="$(git rev-parse "$TIP^{commit}")"
TREE_SHA="$(git rev-parse "$TIP^{tree}")"

rm -rf "$OUT"
mkdir -p "$OUT"

echo "baseline : $BASELINE"
echo "tip      : $TIP_SHA ($TIP)"
echo "tree     : $TREE_SHA"

# The bundle carries the TAG only, never the branch. The branch tip is the
# transport commit that contains this bundle, and a bundle cannot contain the
# commit that contains it. The tag is the delivery, so this is well defined
# however far the branch has moved on.
git bundle create "$OUT/ipo-screening-engine-v1.5.bundle" \
    "refs/tags/$TIP" --not "$BASELINE" >/dev/null

if [ "$EMIT_PATCHES" = "1" ]; then
    mkdir -p "$OUT/patches"
    git format-patch "$BASELINE..$TIP" -o "$OUT/patches" --no-signature -q
fi

( cd "$OUT" && sha256sum ipo-screening-engine-v1.5.bundle > SHA256SUMS )

{
    echo "Carrier verification record for IPO Screening Engine v1.5"
    echo "generated:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "baseline:    $BASELINE"
    echo "tip:         $TIP_SHA ($TIP)"
    echo "tree:        $TREE_SHA"
    echo "diffstat:    $(git diff --shortstat "$BASELINE" "$TIP")"
    echo
    echo "Materialise this exact tree anywhere that has the baseline:"
    echo "  git fetch <bundle> 'refs/tags/$TIP:refs/tags/$TIP'"
    echo "  git checkout -b arena/<new-branch> $TIP"
    echo "  git rev-parse 'HEAD^{tree}'      # -> $TREE_SHA"
    echo
    echo "Fetch the TAG as a tag, not into a branch: the bundle carries"
    echo "'refs/tags/$TIP', and verify-delivery.sh resolves the delivery by that tag,""
    echo "so mapping it to a branch leaves the tag unresolved. Create your working"
    echo "branch from the tag afterwards, as shown."
    echo
    echo "Then confirm it works, not just that the bytes match:"
    echo "  ./handoff/delivery/verify-delivery.sh          # -> ACCEPTED"
    echo "  PYTHONPATH=engine python3 -m pytest tests/ -q  # -> 238 passed"
    echo
    echo "sha256:"
    sed 's/^/  /' "$OUT/SHA256SUMS"
} > "$OUT/VERIFICATION.txt"

echo "--- carrier written to $OUT ---"
ls -la "$OUT"
echo "--- integrity ---"
( cd "$OUT" && sha256sum -c SHA256SUMS )
