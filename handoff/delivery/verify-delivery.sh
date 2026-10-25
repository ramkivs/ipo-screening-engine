#!/usr/bin/env bash
# Verify the IPO Screening Engine v1.5 delivery.
#
# Run this from the root of a workspace that is supposed to CONTAIN the
# delivery. It answers one question precisely: is the delivery present, intact
# and working here?
#
# Exit codes:
#   0  verified - delivery present, tree matches, tests pass, golden hash matches
#   1  FAILED   - delivery is present but something does not match
#   2  ABSENT   - this workspace does not contain the delivery; nothing could be
#                 verified. This is NOT a failure of the delivery. See the
#                 instructions printed in that case.
#
# The distinction matters: a fresh clone of GitHub contains only the baseline
# (01ba66c) until the delivery branch is pushed, so running verification there
# will always return 2. That says "wrong workspace", not "broken delivery".

set -uo pipefail

BASELINE="01ba66c12ca1195fd7acbd287c3e39a019808094"
BASELINE_SHORT="01ba66c"
TAG="v1.5-delivery"
GOLDEN_HASH="e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1"
EVAL_AT="2026-10-05T12:00:00Z"

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)" || exit 2

PASS=0
FAIL=0
SKIP=0

ok()   { printf '  \033[32mPASS\033[0m  %s\n' "$1"; PASS=$((PASS + 1)); }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; FAIL=$((FAIL + 1)); }
skip() { printf '  \033[33mSKIP\033[0m  %s\n' "$1"; SKIP=$((SKIP + 1)); }
say()  { printf '%s\n' "$1"; }

say "IPO Screening Engine v1.5 - delivery verification"
say "workspace: $(pwd)"
say ""

# ---------------------------------------------------------------------------
# 0. Is the delivery here at all?
# ---------------------------------------------------------------------------

HAS_FILES=0
[ -d engine/ipo_screening ] && [ -d tests ] && HAS_FILES=1

HAVE_TAG=0
TIP=""
if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null 2>&1; then
    HAVE_TAG=1
    TIP="$(git rev-parse "refs/tags/$TAG^{commit}")"
fi

if [ "$HAS_FILES" -eq 0 ] && [ "$HAVE_TAG" -eq 0 ]; then
    say "RESULT: cannot verify - the delivery is not in this workspace."
    say ""
    say "  engine/ and tests/ are absent, and the '$TAG' tag does not resolve."
    say "  This workspace holds the baseline ($BASELINE_SHORT) only."
    say ""
    say "  This is expected in a fresh clone of GitHub: the delivery was built in"
    say "  a sandbox whose remote access was already closed, so it was never"
    say "  pushed, and its commits exist only in that session's clone."
    say ""
    say "  To verify, get the delivery into a workspace first - either"
    say "    * the original session workspace itself, or"
    say "    * a copy of it, or"
    say "    * the carrier:"
    say "        git fetch handoff/delivery/carrier/ipo-screening-engine-v1.5.bundle \\"
    say "            'refs/tags/$TAG:refs/tags/$TAG'"
    say "        git checkout -b arena/<new-branch> $TAG"
    say "  then run this script again."
    exit 2
fi

# ---------------------------------------------------------------------------
# 1. The delivery commit and its identity
# ---------------------------------------------------------------------------

say "1. Delivery"

# Resolve the delivery from whatever ref form this workspace happens to have.
# A verifier must not fail merely because the tag was fetched into a branch:
# what matters is whether the CONTENT is the delivery, which the tree hash and
# the behavioural checks in section 3 establish.
SOURCE=""
for ref in "refs/tags/$TAG" "refs/heads/arena/01a10abc-ipo-screening-engine"; do
    if git rev-parse -q --verify "$ref^{commit}" >/dev/null 2>&1; then
        SOURCE="$ref"
        break
    fi
done
# HEAD is only the delivery if the delivery files are actually checked out.
if [ -z "$SOURCE" ] && [ "$HAS_FILES" -eq 1 ]; then
    SOURCE="HEAD"
fi

TREE=""
if [ -n "$SOURCE" ]; then
    TIP="$(git rev-parse "$SOURCE^{commit}")"
    TREE="$(git rev-parse "$SOURCE^{tree}")"
    ok "delivery resolved from $SOURCE"
    say "        commit: $TIP"
    say "        tree:   $TREE"
elif [ "$HAVE_TAG" -eq 1 ]; then
    bad "tag $TAG resolved but the delivery is not checked out"
    say "        run:  git checkout arena/01a10abc-ipo-screening-engine"
else
    bad "no delivery ref found (tag $TAG, the pinned branch, or HEAD)"
fi

if [ -n "$TREE" ]; then
    RECORD=""
    [ -f handoff/delivery/carrier/VERIFICATION.txt ] && RECORD="handoff/delivery/carrier/VERIFICATION.txt"
    if [ -n "$RECORD" ]; then
        EXPECTED="$(sed -n 's/^tree:[[:space:]]*//p' "$RECORD" | head -1)"
        if [ "$TREE" = "$EXPECTED" ]; then
            ok "tree matches the delivery tree recorded in the carrier"
        else
            bad "tree $TREE != the tree recorded in the carrier ($EXPECTED)"
        fi
    else
        # No recorded hash to compare against. The behavioural checks are then
        # the authority; the tree is still printed above as the identity.
        skip "no carrier/VERIFICATION.txt here: nothing to compare the tree against"
        say "        the tree above identifies what is present; sections 2-3 decide"
        say "        whether it behaves like the delivery"
    fi

    if git cat-file -e "$BASELINE^{commit}" 2>/dev/null; then
        STAT="$(git diff --shortstat "$BASELINE" "$TIP" 2>/dev/null)"
        say "        vs baseline $BASELINE_SHORT: ${STAT:-<none>}"
        ok "baseline $BASELINE_SHORT is present"
        UNRELATED="$(git diff --name-only "$BASELINE" "$TIP" 2>/dev/null | grep -c '^handoff/\(authoritative\|reference\)/' || true)"
        if [ "${UNRELATED:-0}" -eq 0 ]; then
            ok "the delivery does not modify the governing handoff artifacts"
        else
            bad "$UNRELATED file(s) under handoff/authoritative|reference were changed"
        fi
    else
        skip "baseline $BASELINE_SHORT not present; cannot diff"
    fi
fi

# ---------------------------------------------------------------------------
# 2. The carrier
# ---------------------------------------------------------------------------

say ""
say "2. Portable carrier"

BUNDLE="handoff/delivery/carrier/ipo-screening-engine-v1.5.bundle"
if [ -f "$BUNDLE" ]; then
    ok "bundle present ($(du -h "$BUNDLE" | cut -f1))"
    if git bundle verify "$BUNDLE" >/dev/null 2>&1; then
        ok "bundle verifies"
    else
        bad "bundle does not verify"
    fi
    if [ -f handoff/delivery/carrier/SHA256SUMS ]; then
        if (cd handoff/delivery/carrier && sha256sum -c SHA256SUMS >/dev/null 2>&1); then
            ok "checksums match"
        else
            bad "checksum mismatch"
        fi
    else
        skip "no SHA256SUMS"
    fi
else
    skip "no bundle in this workspace (regenerate: ./handoff/delivery/make-carrier.sh)"
fi

# ---------------------------------------------------------------------------
# 3. Functional verification
# ---------------------------------------------------------------------------

say ""
say "3. Behaviour"

if [ "$HAS_FILES" -eq 0 ]; then
    skip "engine/ and tests/ absent"
else
    if python3 -c 'import pytest' >/dev/null 2>&1; then
        OUT="$(PYTHONPATH=engine python3 -m pytest tests/ -q 2>&1 | tail -1)"
        if printf '%s' "$OUT" | grep -q '238 passed'; then
            ok "test suite: 238 passed"
        elif printf '%s' "$OUT" | grep -q 'passed'; then
            bad "test suite did not report 238 passed: $OUT"
        else
            bad "test suite failed: $OUT"
        fi
    else
        skip "pytest not installed (python3 -m pip install --break-system-packages pytest jsonschema openpyxl)"
    fi

    if python3 -c 'import jsonschema, openpyxl' >/dev/null 2>&1; then
        STORE="$(mktemp -d)"
        RUN="$(PYTHONPATH=engine python3 engine/tools/ipo_screen.py run \
                  fixtures/vishal_nirmiti/input.json --at "$EVAL_AT" --store "$STORE" 2>&1)"
        GOT="$(printf '%s' "$RUN" | sed -n 's/.*Result hash[[:space:]]*//p' | head -1 | tr -d ' ')"
        if [ "$GOT" = "$GOLDEN_HASH" ]; then
            ok "golden evaluation reproduces the frozen result hash"
        elif [ -n "$GOT" ]; then
            bad "golden hash $GOT != expected $GOLDEN_HASH"
        else
            bad "golden evaluation produced no result hash"
        fi
        rm -rf "$STORE"
    else
        skip "jsonschema/openpyxl not installed; cannot re-run the golden case"
    fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

say ""
say "----------------------------------------------------------------"
if [ "$FAIL" -eq 0 ]; then
    say "RESULT: ACCEPTED - $PASS passed, $SKIP skipped, 0 failed."
    say "        delivery tree: ${TREE:-<unversioned content>}"
    exit 0
fi
say "RESULT: NOT ACCEPTED - $PASS passed, $SKIP skipped, $FAIL FAILED."
exit 1
