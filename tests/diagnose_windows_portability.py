"""Read-only Windows interpreter/evidence probe; stdout is an ASCII JSON receipt.

Run with the SAME Python used by pytest. Only an explicit --output creates a
receipt outside the repository. No checkout repair, install, store write, cache
patch or harness modification is performed.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import asdict
import hashlib
from importlib import metadata
import json
import locale
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"
sys.path.insert(0, str(ENGINE))
PUBLISHED = "dfa34b26a45b672dc92bcaed337e48f7a2b4ca13"
RK = "handoff/reference/U18109WB2010PLC144256-R.K Fashion accessories.pdf"
PARAS = "evidence/non-authoritative/paras-healthcare-issue-terms-20261024"
IG = "evidence/market-observations/investorgain-tonbo-20261015"


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, timeout=30)
    return {"returncode": result.returncode,
            "stdout": result.stdout.decode("utf-8", errors="replace").strip(),
            "stderr": result.stderr.decode("utf-8", errors="replace").strip()}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def capture(path, expected):
    raw = (ROOT / path).read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    return {"path": path, "bytes": len(raw), "sha256": digest(raw),
            "expected": expected.lower(), "matches": digest(raw) == expected.lower(),
            "crlf_count": raw.count(b"\r\n"), "lf_count": raw.count(b"\n"),
            "normalized_lf_sha256": digest(lf),
            "reencoded_crlf_sha256": digest(lf.replace(b"\n", b"\r\n"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-extraction", action="store_true",
                        help="Also build canonical R.K. input, without evaluation or persistence")
    parser.add_argument("--output", type=Path,
                        help="Create a new UTF-8 JSON receipt outside the repository (never overwrite)")
    args = parser.parse_args()
    if args.output and args.output.resolve().is_relative_to(ROOT):
        parser.error("--output must be outside the repository; checkout files are never written")
    report = {"platform": platform.platform(), "python": sys.version,
              "executable": sys.executable, "locale_encoding": locale.getencoding(),
              "preferred_encoding": locale.getpreferredencoding(False),
              "utf8_mode": sys.flags.utf8_mode, "dependencies": {}}
    for package in ("pypdf", "Pillow", "rapidocr", "onnxruntime", "pytest"):
        try:
            report["dependencies"][package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            report["dependencies"][package] = None
    try:
        from PIL import Image
        report["PIL_import"] = {"ok": True, "version": Image.__version__}
    except Exception as exc:
        report["PIL_import"] = {"ok": False, "error": repr(exc)}
    report["git_head"] = git("rev-parse", "HEAD")
    report["git_autocrlf"] = git("config", "--get", "core.autocrlf")
    report["harness_status"] = git("status", "--short", "--", "tests/gmp_mechanics_harness.py")
    try:
        checksum, relative = (ROOT / IG / "SHA256SUMS").read_text(encoding="utf-8").strip().split(maxsplit=1)
        captures = [capture(relative, checksum)]
        manifest = json.loads((ROOT / PARAS / "capture-manifest.json").read_text(encoding="utf-8"))
        captures.extend(capture(f"{PARAS}/{a['file']}", a["sha256"]) for a in manifest["artifacts"])
        report["captures"] = captures
        report["attributes"] = git("check-attr", "text", "eol", "--", *[c["path"] for c in captures])
    except Exception as exc:
        report["capture_error"] = repr(exc)
    try:
        from ipo_screening.extraction.pdf_source import load_pdf_source
        from ipo_screening.extraction.sections import SectionExtractor
        from ipo_screening.extraction.toc import TOCRouter

        doc, reader = load_pdf_source(ROOT / RK)
        router = TOCRouter.from_pdf(reader)
        limits = router.get_page_range("capital_structure")
        sections = SectionExtractor(doc, reader)
        fields = sections.extract_capital_structure({"capital_structure": limits})
        report["rk"] = {"pdf_sha256": doc.content_hash, "pdf_bytes": doc.file_size_bytes,
                        "page_count": doc.page_count, "capital_range": limits,
                        "extractions": [asdict(f) for f in fields],
                        "page_status": sections.page_status, "pages": {}}
        for number in (125, 126):
            text = reader.pages[number - 1].extract_text() or ""
            report["rk"]["pages"][number] = {"utf8_sha256": digest(text.encode("utf-8")), "text": text}
        if args.full_extraction:
            from ipo_screening.extraction import DocumentExtractor
            canonical, extraction = DocumentExtractor().extract_from_pdf(ROOT / RK, allow_fixture_fallbacks=False)
            report["rk"]["canonical_capital_structure"] = canonical["capital_structure"]
            report["rk"]["canonical_capital_evidence"] = {
                k: v for k, v in canonical.get("_evidence", {}).items()
                if k.startswith("capital_structure.")}
            report["rk"]["page_routing"] = extraction.metadata.get("page_routing")
    except Exception as exc:
        report["rk_error"] = repr(exc)
    try:
        # Recover and run the EXACT published child script under this actual
        # interpreter's default encoding (no emulation). Evaluation has no store.
        source = git("show", f"{PUBLISHED}:tests/test_reproducibility_store.py")
        if source["returncode"]:
            raise RuntimeError(source["stderr"])
        function = next(n for n in ast.parse(source["stdout"]).body
                        if isinstance(n, ast.FunctionDef) and n.name == "test_result_hash_is_stable_across_processes")
        script = ast.literal_eval(next(n.value for n in function.body if isinstance(n, ast.Assign)
                                       and any(isinstance(t, ast.Name) and t.id == "script" for t in n.targets)))
        child = subprocess.run([sys.executable, "-c", script, str(ROOT / "fixtures/vishal_nirmiti/input.json")],
                               cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ENGINE)),
                               capture_output=True, timeout=180)
        report["original_repro_child"] = {"returncode": child.returncode,
            "stdout": child.stdout.decode("utf-8", errors="replace"),
            "stderr": child.stderr.decode("utf-8", errors="replace")}
    except Exception as exc:
        report["repro_probe_error"] = repr(exc)
    # ASCII survives legacy Windows consoles; shell redirection may choose its
    # own encoding, so consumers should use a text viewer if needed.
    text = json.dumps(report, ensure_ascii=True, indent=2, default=str)
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n")
        print("Diagnostic JSON written (UTF-8); checkout unchanged.")
    else:
        print(text)


if __name__ == "__main__":
    main()
