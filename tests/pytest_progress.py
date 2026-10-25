"""Live progress reporting for the long backend suite (``tests/pytest_progress.py``).

Why this exists
---------------
A full run of ``tests/`` extracts real filing PDFs (a 591-page and a 450-page
document are opened repeatedly), so it takes tens of minutes.  pytest's own
output is block-buffered when stdout is redirected to a file or a pipe, which
made long runs look stalled: nothing appeared until a buffer flushed.  This
plugin writes progress to **stderr with an explicit flush** and reports the
quantities that are actually knowable:

* completed tests against the number collected (that is a completion count, not
  a forecast — the printed percentage is "of collected tests", and the ETA is a
  linear extrapolation from the measured rate, labelled as such);
* a stage marker per test module with its own elapsed time, so the slow part of
  the run is identifiable without ``--durations``;
* a one-line summary at the end.

Activate it explicitly (``-p pytest_progress``, run from the repository root) or
via ``addopts`` in ``pytest.ini``.  Frequency: every 25 completed tests by
default, ``PYTEST_PROGRESS_EVERY=10`` to change it; ``PYTEST_PROGRESS_MODULES=0``
to drop the per-module markers.

It never alters collection, selection, skipping or results: it only reads
reports.  See "Test duration and progress" in ``docs/RUNBOOK.md``.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Dict, List, Optional

import pytest


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except ValueError:  # pragma: no cover - defensive
        return default


def _emit(text: str) -> None:
    # stderr, flushed: visible while the run is still going even when stdout is
    # redirected to a log file.
    print(text, file=sys.stderr, flush=True)


class PytestProgress:
    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.total = 0
        self.done = 0
        self.counts: Dict[str, int] = {"passed": 0, "failed": 0, "skipped": 0}
        self.started: Optional[float] = None
        self.every = _env_int("PYTEST_PROGRESS_EVERY", 25)
        self.want_modules = os.environ.get("PYTEST_PROGRESS_MODULES", "1") != "0"
        self.bar_width = 30
        self.current_module: Optional[str] = None
        self.module_started: float = 0.0
        self.module_tests = 0
        self.slowest: List[tuple] = []

    # -- lifecycle ----------------------------------------------------------
    @pytest.hookimpl(tryfirst=True)
    def pytest_report_collectionfinish(self, config, start_path, items) -> str:
        self.total = len(items)
        self.started = time.monotonic()
        _emit(f"[pytest-progress] collected {self.total} tests; start "
              f"{time.strftime('%H:%M:%S')}")
        return ""  # keep it off stdout so the plugin's line is the only channel

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logreport(self, report) -> None:
        # One tick per test: the call phase, or a skip/fail decided in setup.
        if report.when == "call" or (
            report.when == "setup" and report.outcome in ("skipped", "failed")
        ):
            self.done += 1
            key = report.outcome if report.outcome in self.counts else "passed"
            self.counts[key] += 1
            duration = getattr(report, "duration", 0.0) or 0.0
            if duration >= 10.0:
                self.slowest.append((duration, report.nodeid))
            self._maybe_draw()

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logfinish(self, nodeid, location) -> None:
        if not self.want_modules:
            return
        module = str(location[0]) if location else "?"
        if module != self.current_module:
            now = time.monotonic()
            if self.current_module is not None and self.module_tests:
                _emit(
                    f"[pytest-progress]   stage {self.current_module}: "
                    f"{self.module_tests} tests, {now - self.module_started:.1f}s"
                )
            self.current_module = module
            self.module_started = now
            self.module_tests = 0
        self.module_tests += 1

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionfinish(self, session, exitstatus) -> None:
        now = time.monotonic()
        if self.current_module is not None and self.module_tests and self.started:
            _emit(
                f"[pytest-progress]   stage {self.current_module}: "
                f"{self.module_tests} tests, {now - self.module_started:.1f}s"
            )
        if self.started:
            _emit(
                f"[pytest-progress] finished {self.done}/{self.total} tests in "
                f"{now - self.started:.1f}s (passed={self.counts['passed']} "
                f"failed={self.counts['failed']} skipped={self.counts['skipped']}), "
                f"exitstatus={int(exitstatus)}"
            )
            if self.slowest:
                for dur, nodeid in sorted(self.slowest, reverse=True)[:8]:
                    _emit(f"[pytest-progress]   slow test {dur:7.1f}s  {nodeid}")

    # -- drawing ------------------------------------------------------------
    def _maybe_draw(self) -> None:
        if self.done % self.every and self.done != self.total:
            return
        self._draw()

    def _draw(self) -> None:
        total = self.total or 1
        pct = 100.0 * self.done / total
        filled = int(round(self.bar_width * self.done / total))
        bar = "#" * filled + "." * (self.bar_width - filled)
        now = time.monotonic()
        elapsed = (now - self.started) if self.started else 0.0
        rate = self.done / elapsed if elapsed > 0 and self.done else 0.0
        remaining = (total - self.done) / rate if rate else 0.0
        line = (
            f"[pytest-progress] |{bar}| {pct:5.1f}% of collected "
            f"{self.done}/{total}  elapsed {elapsed:.0f}s  "
            f"eta {remaining:.0f}s (linear-rate estimate)"
        )
        if self.counts["failed"]:
            line += f"  FAILURES={self.counts['failed']}"
        _emit(line)


def pytest_configure(config: pytest.Config) -> None:
    plugin = PytestProgress(config)
    config._pytest_progress = plugin
    config.pluginmanager.register(plugin, "pytest-progress")


def pytest_unconfigure(config: pytest.Config) -> None:
    plugin = getattr(config, "_pytest_progress", None)
    if plugin is not None:
        config.pluginmanager.unregister(plugin)
        config._pytest_progress = None
