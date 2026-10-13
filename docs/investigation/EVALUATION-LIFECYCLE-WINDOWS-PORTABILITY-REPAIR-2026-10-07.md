# Evaluation Lifecycle Windows Portability & Cross-Platform Locking Repair

**Document Version:** 1.0.0  
**Date:** 2026-10-07  
**Branch:** `arena/01a10b42-ipo-screening-engine`  
**Base Commit:** `39d9a35741170057e5b6b115d68266d9042d7390`  
**Protected Main:** `01ba66c12ca1195fd7acbd287c3e39a019808094`  
**Classification:** Incident Root-Cause Analysis, Architectural Repair & Cross-Platform Verification

---

## 1. Executive Summary & Incident Root Cause

### 1.1 The Incident
During native Windows verification of the newly delivered Evaluation Lifecycle subsystem (commit `39d9a357`), executing standard top-level package import failed:

```
ModuleNotFoundError: No module named 'fcntl'
```

**Import Trace:**
```
engine/ipo_screening/__init__.py
  -> imports engine/ipo_screening/lifecycle.py
      -> imports fcntl  (line 31)
```

### 1.2 Root Cause Analysis
The Python standard library `fcntl` module provides interfaces to the POSIX file-locking system calls (`flock`, `fcntl`). It is built strictly on Unix/POSIX systems (Linux, macOS, BSD) and is **not provided on Windows**.

Because `engine/ipo_screening/__init__.py` exposed the lifecycle public symbols (`LifecycleManager`, `LifecycleRecord`, `LifecycleIndex`, etc.), importing `ipo_screening` unconditionally imported `lifecycle.py`, triggering the unconditional import of `fcntl`. Consequently, on Windows, any script importing `ipo_screening` failed immediately during module initialization.

---

## 2. Locking Mechanism: Before vs. After

### 2.1 Locking Mechanism Before (POSIX-Only)
In `39d9a35741170057e5b6b115d68266d9042d7390`:
```python
# lifecycle.py (line 31)
import fcntl

# LifecycleManager._file_lock (lines 321-329)
@contextlib.contextmanager
def _file_lock(self):
    """Acquire POSIX file lock to ensure atomic multi-process transitions."""
    self.root.mkdir(parents=True, exist_ok=True)
    with open(self.lock_path, "w") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
```

**Defects & Platform Limitations:**
1. **Windows Import Blocker**: Module-level `import fcntl` halts import on all NT platforms.
2. **File Truncation Contention**: Opening with mode `"w"` invokes `CREATE_ALWAYS` / `TRUNCATE_EXISTING`. On Windows, if a process holds an exclusive byte lock on a file, another process attempting to open with `"w"` encounters `PermissionError: [WinError 33] The process cannot access the file because another process has locked a portion of the file`.
3. **No Timeout / Deadlock Protection**: Indefinite blocking with `LOCK_EX` without fail-closed timeout guards.

### 2.2 Exact Replacement Mechanism (Cross-Platform)
The repair introduces safe optional platform imports, cross-platform locking primitives (`acquire_file_lock` and `release_file_lock`), and an in-process thread safety layer:

```python
try:
    import fcntl
except (ImportError, ModuleNotFoundError):
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except (ImportError, ModuleNotFoundError):
    msvcrt = None  # type: ignore[assignment]
```

#### Primitives Specification:
1. **POSIX Environments (`fcntl` is not None)**:
   - Uses `fcntl.flock(fileno, fcntl.LOCK_EX)` or non-blocking polling `fcntl.flock(fileno, fcntl.LOCK_EX | fcntl.LOCK_NB)` with a strict monotonic timeout.
   - Unlocks via `fcntl.flock(fileno, fcntl.LOCK_UN)`.
   - OS kernel automatically releases advisory locks upon process crash or descriptor close.

2. **Windows Environments (`msvcrt` is not None)**:
   - Uses native standard-library `msvcrt.locking(fileno, msvcrt.LK_NBLCK, 1)` on byte 0 of the lock file.
   - If contested, retries at 10 ms intervals until acquired or until `timeout` expires (default 30.0s).
   - Unlocks via `msvcrt.locking(fileno, msvcrt.LK_UNLCK, 1)` on byte 0.
   - Win32 kernel automatically releases byte-range locks upon process termination or handle closure.

3. **Lock File Lifecycle & Append Mode**:
   - The lock file `<store_root>/lifecycle_index.lock` is opened in append/update mode (`"a+b"`), ensuring that:
     * The file is created if missing.
     * The file is **never truncated**, eliminating Windows `ERROR_LOCK_VIOLATION` during file opening.
     * At least 1 byte (`b"0"`) is present to provide the byte target required for Windows `LockFile` / `_locking`.

4. **Multi-Threading + Multi-Processing Protection**:
   - `LifecycleManager` incorporates `self._thread_lock = threading.RLock()` to serialize threads in the same process before invoking the OS-level file lock, optimizing multi-threaded performance while maintaining cross-process exclusion.

---

## 3. Critical-Section Boundary & Failure Semantics

### 3.1 Critical Section Boundary
The lock strictly encompasses the exact critical sections previously protected:
- `LifecycleManager.register_evaluation`: Load index, validate active policy, demote incumbent active, link acyclic lineage, persist evaluation sibling `lifecycle.json`, and atomically persist `lifecycle_index.json`.
- `LifecycleManager.archive_evaluation`: Load index, verify Tier 1 golden protection, verify offering status, update visibility to `ARCHIVED`, write sibling `lifecycle.json`, and persist `lifecycle_index.json`.
- `LifecycleManager.unarchive_evaluation`: Load index, update visibility to `VISIBLE`, write sibling `lifecycle.json`, and persist `lifecycle_index.json`.
- `LifecycleManager.make_active`: Load index, verify ratified configuration baseline, detect DAG cycles (`_detect_cycle`), demote incumbent active to `SUPERSEDED`, designate target as `ACTIVE`, write sibling `lifecycle.json`, and persist `lifecycle_index.json`.

### 3.2 Failure Semantics (Strictly Fail-Closed)
- If lock acquisition fails (e.g., timeout exceeded under unresolvable deadlock or extreme contention), `acquire_file_lock` raises `TimeoutError` **before** entering the critical section (`yield`).
- The mutation is **never** executed without holding the exclusive lock.
- Silent downgrades to unlocked writes are strictly forbidden.
- On any exception occurring within the critical section, the `finally:` block executes `release_file_lock(fileno)`, guaranteeing that no dangling locks persist.

---

## 4. Verification Evidence Matrix

### 4.1 Linux / POSIX Verification (Arena Environment)
**Status: VERIFIED ON ARENA/LINUX — PASS**

Full test execution on Linux x86_64 Debian/Ubuntu container:

| Test Suite | Tests Run | Result | Key Invariants Verified |
| :--- | :--- | :--- | :--- |
| `tests/test_evaluation_lifecycle.py` | 26 passed | **PASS** | Tests A–S, mutual exclusion, release on completion, release on exception, Windows simulation, fail-closed timeout, index atomic replacement |
| `frontend/test/*.test.js` | 55 passed | **PASS** | Read-only protocol, zero client calculation, zero delete controls, distinction banners |
| `tests/test_vishal_golden.py` | 19 passed | **PASS** | Bit-for-bit golden evaluation hash `e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1` |
| `tests/test_rk_fashion_reconciliation.py` | 5 passed | **PASS** | R.K. Fashion score strictly 50.0/100 (DEFECT-1 supplier, DEFECT-2 domestic CAGR, DEFECT-3 statutory CFO) |
| `tests/test_ui7_ingestion.py` | 16 passed | **PASS** | Fail-closed statutory ingestion, zero fixture fallbacks, multi-IPO coexistence |
| `tests/test_presentation_api.py` | 21 passed | **PASS** | OpenAPI schema compliance, history filtering, lifecycle endpoints, read-only middleware |
| `tests/test_acceptance_matrix.py` | 55 passed | **PASS** | Acceptance criteria for engine phases 1 through 6 |
| `tests/test_reproducibility_store.py` | 32 passed | **PASS** | Immutability and store verification |
| `tests/test_dataset_phase6b.py` | 30 passed | **PASS** | Backtest dataset extraction |
| `tests/test_analytics_phase6c.py` | 40 passed | **PASS** | Post-listing analytics |
| `tests/test_calibration_phase6d.py` | 56 passed | **PASS** | Calibration proposal generation |

### 4.2 Native Windows Verification
**Status: WINDOWS EXECUTION NOT AVAILABLE IN ARENA**

Because Arena executes within a Linux container environment without native Windows kernel execution or Wine, native Windows testing cannot be executed directly within Arena.

#### Precise Host Verification Commands for Local Windows Checkout:
Once pulled to your Windows workstation, run the following verification commands in PowerShell:

```powershell
# 1. Pull the repair commit
git fetch origin
git checkout arena/01a10b42-ipo-screening-engine
git pull --ff-only origin arena/01a10b42-ipo-screening-engine

# 2. Verify top-level import without fcntl error
python -c "import ipo_screening; print('Windows import successful:', ipo_screening.ENGINE_VERSION)"

# 3. Verify lifecycle module and locking primitives
python -c "from ipo_screening.lifecycle import LifecycleManager, acquire_file_lock, release_file_lock; print('Lifecycle locking loaded successfully')"

# 4. Run the full lifecycle test suite on Windows
pytest tests/test_evaluation_lifecycle.py -v

# 5. Run golden evaluation bit-for-bit check
pytest tests/test_vishal_golden.py -v
```

---

## 5. Scope & Invariants Audit

### 5.1 Frozen Core Audit
Zero changes made to the frozen core:
- `engine/ipo_screening/derived.py`: UNCHANGED
- `engine/ipo_screening/scoring.py`: UNCHANGED
- `engine/ipo_screening/knockouts.py`: UNCHANGED
- `engine/ipo_screening/snapshots.py`: UNCHANGED
- `engine/ipo_screening/evaluation.py`: UNCHANGED
- `engine/ipo_screening/extraction/price_band_notice.py`: UNCHANGED

### 5.2 Storage & Evaluation Artifacts Audit
Zero changes made to existing evaluations:
- `evaluation.json`: UNCHANGED
- `input.json`: UNCHANGED
- `evidence.json`: UNCHANGED
- `market.json`: UNCHANGED
- `peers.json`: UNCHANGED
- `result.json`: UNCHANGED
- `manifest.json`: UNCHANGED
- `observations/`: UNCHANGED

### 5.3 Changed Files Summary
Only two files were modified:
1. `engine/ipo_screening/lifecycle.py`: Replaced unconditional `fcntl` import with cross-platform primitives (`acquire_file_lock`, `release_file_lock`) supporting POSIX and Windows `msvcrt.locking`, plus append-mode non-truncating lock file handling.
2. `tests/test_evaluation_lifecycle.py`: Added 7 focused tests covering import portability without `fcntl`, writer serialization, normal release, exception release, Windows `msvcrt` simulation, fail-closed timeout, and index atomic replacement integrity.
