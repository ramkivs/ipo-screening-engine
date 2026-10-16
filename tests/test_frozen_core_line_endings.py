from pathlib import Path

from ipo_screening.post_listing.v16_implementation import (
    FROZEN_CORE_HASHES,
    verify_frozen_core,
)


def _prepare_fixture(root: Path, line_ending: bytes) -> None:
    repository = Path.cwd()

    for relative_path in FROZEN_CORE_HASHES:
        source = (repository / relative_path).read_bytes()
        source = source.replace(b"\r\n", b"\n")

        if line_ending == b"\r\n":
            source = source.replace(b"\n", b"\r\n")

        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source)


def test_frozen_core_accepts_lf_files(tmp_path: Path) -> None:
    _prepare_fixture(tmp_path, b"\n")

    verified, results = verify_frozen_core(base_dir=tmp_path)

    assert verified is True
    assert all(results.values())


def test_frozen_core_accepts_crlf_files(tmp_path: Path) -> None:
    _prepare_fixture(tmp_path, b"\r\n")

    verified, results = verify_frozen_core(base_dir=tmp_path)

    assert verified is True
    assert all(results.values())


def test_frozen_core_rejects_real_content_change(tmp_path: Path) -> None:
    _prepare_fixture(tmp_path, b"\r\n")

    relative_path = next(iter(FROZEN_CORE_HASHES))
    target = tmp_path / relative_path
    target.write_bytes(target.read_bytes() + b"\n# unauthorized change\n")

    verified, results = verify_frozen_core(base_dir=tmp_path)

    assert verified is False
    assert results[relative_path] is False
    assert all(
        result
        for path, result in results.items()
        if path != relative_path
    )
