#!/usr/bin/env bash
# Regenerate handoff/delivery/MANIFEST.sha256.
#
# The manifest lists a SHA-256 for every file this delivery adds or changes, so
# a workspace can prove its own contents are intact without any external record.
# That matters because the delivery cannot contain its own tree hash (writing the
# hash into a file changes the hash), and the carrier that does record it is
# transport-only.
#
# It covers files changed against the baseline, and deliberately excludes:
#   * itself                                     (a file cannot list its own hash)
#   * handoff/delivery/carrier/                  (transport-only, regenerated)
#   * handoff/delivery/download/                 (staged copies)
#
# It must be regenerated whenever a delivery file changes, and always BEFORE the
# delivery commit is created, so that the hashes describe the committed contents.
# verify-delivery.sh checks the result.

set -euo pipefail

BASELINE="${BASELINE:-01ba66c12ca1195fd7acbd287c3e39a019808094}"
OUT="handoff/delivery/MANIFEST.sha256"

cd "$(git rev-parse --show-toplevel)"

git cat-file -e "$BASELINE^{commit}" 2>/dev/null || {
    echo "error: baseline $BASELINE is not present in this clone." >&2
    exit 1
}

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

# Files this delivery adds or changes, minus the transport-only paths.
git diff --name-only "$BASELINE" HEAD \
    | grep -v -E '^handoff/delivery/(carrier|download)/' \
    | grep -v -x 'handoff/delivery/MANIFEST.sha256' \
    | LC_ALL=C sort > "$TMP"

missing=0
while IFS= read -r path; do
    [ -e "$path" ] || { echo "error: listed file is absent: $path" >&2; missing=1; }
done < "$TMP"
[ "$missing" -eq 0 ] || {
    echo "error: working tree does not match the file list; refusing to write a" >&2
    echo "       manifest that would not verify." >&2
    exit 1
}

xargs -a "$TMP" sha256sum > "$OUT"

echo "$(wc -l < "$TMP") files listed in $OUT"
echo "--- self check ---"
sha256sum -c "$OUT" | tail -3
echo "(all lines must read OK)"
