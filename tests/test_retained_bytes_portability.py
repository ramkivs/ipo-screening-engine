"""Keep hash-pinned captures byte-identical under Git CRLF checkout settings."""
import json
import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
IG = "evidence/market-observations/investorgain-tonbo-20261015/rendered-page-capture.md"
PARAS = "evidence/non-authoritative/paras-healthcare-issue-terms-20261024"


@pytest.mark.parametrize("autocrlf", ["true", "input"])
def test_fresh_retained_capture_checkout_preserves_bytes(tmp_path, autocrlf):
    # A private index/work tree exercises Git's actual checkout conversion, not
    # Python newline replacement. Never reset/clean/change the user's index.
    manifest = json.loads((ROOT / PARAS / "capture-manifest.json").read_text(encoding="utf-8"))
    paths = [IG] + [f"{PARAS}/{a['file']}" for a in manifest["artifacts"]]
    git_dir = subprocess.check_output(
        ["git", "rev-parse", "--absolute-git-dir"], cwd=ROOT, text=True
    ).strip()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
    env = dict(os.environ, GIT_INDEX_FILE=str(tmp_path / "index"), GIT_ATTR_NOSYSTEM="1")
    command = ["git", f"--git-dir={git_dir}", f"--work-tree={checkout}",
               "-c", f"core.autocrlf={autocrlf}", "-c", "core.eol=crlf",
               "-c", f"core.attributesFile={os.devnull}"]
    subprocess.run(command + ["read-tree", "HEAD"], cwd=checkout, env=env, check=True)
    subprocess.run(command + ["checkout-index", "--force", "--", *paths, "README.md"],
                   cwd=checkout, env=env, check=True)
    for path in paths:
        original = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)
        assert (checkout / path).read_bytes() == original, path
    if autocrlf == "true":
        # Positive control: conversion really is enabled outside protected paths.
        assert b"\r\n" in (checkout / "README.md").read_bytes()
