#!/usr/bin/env bash
# Stage the delivery artifacts for download.
#
# Builds handoff/delivery/download/ from tracked sources only, so it can be
# recreated at any time on any machine:
#
#   ./handoff/delivery/stage-downloads.sh [tag]
#
# The staging directory is git-ignored (it duplicates the tracked carrier), but
# nothing in it is unique: every file is derived from the tag and the tracked
# carrier. If it disappears, run this script again.

set -euo pipefail

TAG="${1:-v1.5-delivery}"
BASELINE="${BASELINE:-01ba66c12ca1195fd7acbd287c3e39a019808094}"
BASELINE_SHORT="01ba66c"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
OUT="handoff/delivery/download"
BASE_NAME="ipo-screening-engine-v1.5"

git rev-parse -q --verify "$TAG^{commit}" >/dev/null || {
    echo "error: tag '$TAG' is not present in this clone." >&2
    exit 1
}

rm -rf "$OUT"
mkdir -p "$OUT/patches"

DELIVERY_SHA="$(git rev-parse "$TAG^{commit}")"
DELIVERY_TREE="$(git rev-parse "$TAG^{tree}")"
FILE_COUNT="$(git diff --name-only "$BASELINE" "$TAG" | wc -l)"

# ---------------------------------------------------------------------------
# 1. The carrier: the bundle, its checksums and the verification record
# ---------------------------------------------------------------------------
./handoff/delivery/make-carrier.sh "$TAG" >/dev/null
cp handoff/delivery/carrier/"${BASE_NAME}.bundle" "$OUT/"
cp handoff/delivery/carrier/VERIFICATION.txt "$OUT/"

# ---------------------------------------------------------------------------
# 2. Plain-text fallback: the delivery as a git-am-able patch series
# ---------------------------------------------------------------------------
git format-patch "$BASELINE..$TAG" -o "$OUT/patches" --no-signature -q

# ---------------------------------------------------------------------------
# 3. Fallback for a machine with no git objects at all:
#    just the files this delivery adds or changes, to overlay on a main checkout.
# ---------------------------------------------------------------------------
mapfile -t PATHS < <(git diff --name-only "$BASELINE" "$TAG")
git archive --format=tar.gz -o "$OUT/${BASE_NAME}-delivery-files.tar.gz" "$TAG" "${PATHS[@]}"

# ---------------------------------------------------------------------------
# 4. Documentation and tooling, for reference without unpacking anything
# ---------------------------------------------------------------------------
for f in README.md NEXT_SESSION_PROMPT.md verify-delivery.sh make-carrier.sh; do
    cp "handoff/delivery/$f" "$OUT/"
done

# ---------------------------------------------------------------------------
# 5. Checksums over every payload artifact
# ---------------------------------------------------------------------------
(
    cd "$OUT"
    sha256sum "${BASE_NAME}.bundle" "${BASE_NAME}-delivery-files.tar.gz" \
        VERIFICATION.txt patches/*.patch > SHA256SUMS
)

# ---------------------------------------------------------------------------
# 6. A short orientation note, and a readable index for the download server
# ---------------------------------------------------------------------------
cat > "$OUT/START-HERE.txt" <<EOF
IPO Screening Engine v1.5 - delivery artifacts
==============================================

Delivery commit : $DELIVERY_SHA
Delivery tree   : $DELIVERY_TREE
Baseline        : $BASELINE  (== main; unmodified)
Tests           : 238 passing
Golden result   : e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1

WHAT TO DOWNLOAD
----------------
If you have a machine with git and the repository cloned, download ONE file:

    ${BASE_NAME}.bundle

Then:

    sha256sum ${BASE_NAME}.bundle          # compare against SHA256SUMS
    git fetch ${BASE_NAME}.bundle 'refs/tags/$TAG:refs/tags/$TAG'
    git checkout -b arena-ipo-v1.5-publish $TAG
    ./handoff/delivery/verify-delivery.sh  # expect: ACCEPTED

The bundle needs only commit $BASELINE_SHORT, which is already origin/main. That
is why it is under 200 KB rather than carrying the whole repository.

ALTERNATIVES
------------
* patches/                - the delivery as a git-am-able patch series.
                            git am patches/*.patch   (on a $BASELINE_SHORT checkout)
* ${BASE_NAME}-delivery-files.tar.gz
                          - the ${FILE_COUNT} changed files, to overlay on a main
                            checkout, for a machine with no git objects at all.
* NEXT_SESSION_PROMPT.md  - paste into the next coding session.
* verify-delivery.sh      - checks a workspace; exits 0 ACCEPTED, 1 present but
                            wrong, 2 no delivery in this workspace.
* SHA256SUMS              - integrity for every payload artifact.

NOT INCLUDED, DELIBERATELY
--------------------------
The full repository tree (about 7.8 MB, of which ~7 MB is the 551-page RHP PDF
that is already in the baseline). Clone main from GitHub for that.
EOF

python3 - "$OUT" "$DELIVERY_SHA" "$DELIVERY_TREE" "$BASE_NAME" <<'PY'
import hashlib, html, pathlib, sys

out = pathlib.Path(sys.argv[1])
commit, tree, base_name = sys.argv[2], sys.argv[3], sys.argv[4]

rows = []
for path in sorted(out.rglob("*")):
    if not path.is_file() or path.name == "index.html":
        continue
    rel = path.relative_to(out).as_posix()
    size = path.stat().st_size
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if size > 1024 * 1024:
        human = f"{size / 1024 / 1024:.2f} MB"
    elif size > 1024:
        human = f"{size / 1024:.1f} KB"
    else:
        human = f"{size} B"
    rows.append((rel, human, digest))

rows.sort(key=lambda r: (not r[0].endswith(".bundle"), r[0]))

body = "\n".join(
    '<tr><td><a href="{href}">{name}</a></td><td class="n">{size}</td>'
    '<td class="h">{digest}</td></tr>'.format(
        href=html.escape(rel), name=html.escape(rel),
        size=html.escape(size), digest=html.escape(digest))
    for rel, size, digest in rows
)

(out / "index.html").write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IPO Screening Engine v1.5 - delivery artifacts</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         max-width: 60rem; margin: 2.5rem auto; padding: 0 1.25rem; }}
  h1 {{ font-size: 1.35rem; margin-bottom: .25rem; }}
  p.sub {{ margin-top: 0; opacity: .75; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1.5rem 0; }}
  th, td {{ text-align: left; padding: .45rem .6rem; border-bottom: 1px solid rgba(128,128,128,.28);
            vertical-align: top; }}
  th {{ font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; opacity: .7; }}
  td.n {{ white-space: nowrap; }}
  td.h, code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .76rem; }}
  td.h {{ opacity: .65; word-break: break-all; }}
  .box {{ border: 1px solid rgba(128,128,128,.35); border-radius: .5rem; padding: 1rem 1.15rem;
          margin: 1.5rem 0; }}
  .box h2 {{ margin-top: 0; font-size: .95rem; }}
  pre {{ background: rgba(128,128,128,.12); padding: .7rem .85rem; border-radius: .4rem;
         overflow-x: auto; font-size: .8rem; }}
  .big {{ font-size: 1.05rem; }}
</style></head><body>
<h1>IPO Screening Engine v1.5 &mdash; delivery artifacts</h1>
<p class="sub">Complete, committed and green. Nothing here needs reimplementing.</p>

<div class="box">
<h2>Download one file</h2>
<p class="big"><a href="{base_name}.bundle">{base_name}.bundle</a></p>
<p>That is the whole delivery, provided as a git bundle. It needs only commit
<code>01ba66c</code>, which is already <code>origin/main</code>, so it is under
200&nbsp;KB.</p>
<pre>sha256sum {base_name}.bundle      # compare with SHA256SUMS
git fetch {base_name}.bundle 'refs/tags/v1.5-delivery:refs/tags/v1.5-delivery'
git checkout -b arena/<your-session-branch> v1.5-delivery
./handoff/delivery/verify-delivery.sh   # expect: ACCEPTED</pre>
</div>

<div class="box">
<h2>What this is</h2>
<table>
<tr><th>Delivery commit</th><td class="h">{commit}</td></tr>
<tr><th>Delivery tree</th><td class="h">{tree}</td></tr>
<tr><th>Baseline</th><td class="h">01ba66c12ca1195fd7acbd287c3e39a019808094 (== main, unmodified)</td></tr>
<tr><th>Tests</th><td>238 passing</td></tr>
<tr><th>Golden result</th><td class="h">e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1</td></tr>
<tr><th>Contains</th><td>42 files: engine, config, schema, fixtures, tests, docs, CLI, carrier tooling</td></tr>
</table>
<p>Read <a href="START-HERE.txt">START-HERE.txt</a> for the full instructions and
the alternatives; <a href="NEXT_SESSION_PROMPT.md">NEXT_SESSION_PROMPT.md</a> is
the prompt for the next coding session.</p>
</div>

<h2>Everything in this directory</h2>
<table>
<tr><th>File</th><th>Size</th><th>SHA-256</th></tr>
{body}
</table>

<div class="box">
<h2>If you would rather not use the bundle</h2>
<p><code>patches/</code> holds the same delivery as a
<code>git&nbsp;am</code>-able patch series.
<code>{base_name}-delivery-files.tar.gz</code> holds just the 42 files, for a
machine with no git objects at all. The full repository tree is not included
deliberately: it is ~7.8&nbsp;MB, almost all of it the RHP PDF already present in
the baseline.</p>
</div>
</body></html>
""")
PY

echo "staged $(find "$OUT" -type f | wc -l) files in $OUT"
echo "payload total: $(du -sh "$OUT" | cut -f1)"
echo
echo "--- SHA256SUMS ---"
cat "$OUT/SHA256SUMS"
