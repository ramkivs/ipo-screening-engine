"""Phase 6A: Deterministic historical price ingestion adapter.

Parses Bhavcopy CSV and JSON price files, enforces strict fail-closed validation
(no negative prices, no conflicting duplicates, malformed row rejection),
and computes cryptographic provenance hashes.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .trading_calendar import parse_iso_date, format_iso_date


class PriceAdapterError(Exception):
    """Base error for price ingestion failures."""
    pass


class NegativePriceError(PriceAdapterError):
    """Raised when any price point is negative."""
    pass


class DuplicatePriceConflictError(PriceAdapterError):
    """Raised when conflicting price observations exist for the same symbol and date."""
    pass


class MalformedPriceDataError(PriceAdapterError):
    """Raised when input rows violate schema or numeric requirements."""
    pass


@dataclass(frozen=True)
class DailyPriceRecord:
    """A single validated daily price record."""
    date: str  # YYYY-MM-DD
    symbol: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: float = 0.0
    volume: Optional[float] = None
    corporate_action_factor: float = 1.0


@dataclass
class PriceDataset:
    """Collection of ingested daily prices with audit provenance."""
    source_path: str
    source_type: str
    content_hash: str
    trading_dates: Set[str] = field(default_factory=set)
    # Mapping of symbol -> {date: DailyPriceRecord}
    records_by_symbol: Dict[str, Dict[str, DailyPriceRecord]] = field(default_factory=dict)
    # Benchmark symbol mapping -> {date: float}
    benchmarks: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def get_price(self, symbol: str, date_str: str) -> Optional[DailyPriceRecord]:
        return self.records_by_symbol.get(symbol.upper(), {}).get(date_str)

    def get_benchmark_close(self, symbol: str, date_str: str) -> Optional[float]:
        return self.benchmarks.get(symbol.upper(), {}).get(date_str)


def compute_file_sha256(file_path: str | Path) -> str:
    """Compute the SHA-256 digest of a file's raw bytes."""
    path = Path(file_path)
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


BENCHMARK_SYMBOLS = {
    "NIFTY_50_TRI",
    "NIFTY 50 TRI",
    "NIFTY_50",
    "NIFTY 50",
    "NIFTY50",
    "^NSEI",
    "NIFTY_50_INDEX",
    "SENSEX",
    "BSE_SENSEX",
}


def normalize_benchmark_symbol(symbol: str) -> str:
    s = symbol.strip().upper().replace(" ", "_")
    if s in ("NIFTY_50_TRI", "NIFTY50_TRI"):
        return "NIFTY_50_TRI"
    if s in ("NIFTY_50", "NIFTY50", "^NSEI", "NIFTY_50_INDEX"):
        return "NIFTY_50"
    return s


def load_price_file(file_path: str | Path) -> PriceDataset:
    """Load and strictly validate a price file (CSV or JSON)."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"price file not found: {path}")

    content_hash = compute_file_sha256(path)
    source_type = "CSV_BHAVCOPY" if path.suffix.lower() == ".csv" else "JSON_PRICE_FEED"

    if path.suffix.lower() == ".json":
        return _load_json(path, content_hash, source_type)
    else:
        return _load_csv(path, content_hash, source_type)


def _load_csv(path: Path, content_hash: str, source_type: str) -> PriceDataset:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise MalformedPriceDataError("price CSV has no header row")

        # Map field names
        field_map = {fn.strip().upper(): fn for fn in reader.fieldnames}
        
        # Check required columns
        date_col = next((field_map[k] for k in ["DATE", "TRADEDATE", "TRADE_DATE", "TIMESTAMP"] if k in field_map), None)
        symbol_col = next((field_map[k] for k in ["SYMBOL", "SERIES_SYMBOL", "TICKER", "SECURITY"] if k in field_map), None)
        close_col = next((field_map[k] for k in ["CLOSE", "CLOSEPRICE", "CLOSE_PRICE", "SETTLE"] if k in field_map), None)

        if not (date_col and symbol_col and close_col):
            raise MalformedPriceDataError(f"price CSV missing required columns (found: {reader.fieldnames})")

        open_col = next((field_map[k] for k in ["OPEN", "OPENPRICE", "OPEN_PRICE"] if k in field_map), None)
        high_col = next((field_map[k] for k in ["HIGH", "HIGHPRICE", "HIGH_PRICE"] if k in field_map), None)
        low_col = next((field_map[k] for k in ["LOW", "LOWPRICE", "LOW_PRICE"] if k in field_map), None)
        vol_col = next((field_map[k] for k in ["VOLUME", "TOTTRDQTY", "QTY", "TOTAL_QUANTITY"] if k in field_map), None)
        factor_col = next((field_map[k] for k in ["CORPORATE_ACTION_FACTOR", "ADJ_FACTOR", "FACTOR"] if k in field_map), None)

        dataset = PriceDataset(
            source_path=str(path),
            source_type=source_type,
            content_hash=content_hash,
        )

        for row_idx, row in enumerate(reader, start=2):
            raw_date = row.get(date_col)
            raw_sym = row.get(symbol_col)
            raw_close = row.get(close_col)

            if not raw_date or not raw_sym or raw_close is None or raw_close == "":
                raise MalformedPriceDataError(f"row {row_idx}: missing date, symbol, or close")

            try:
                dt = parse_iso_date(raw_date.strip())
                date_str = format_iso_date(dt)
            except Exception as e:
                raise MalformedPriceDataError(f"row {row_idx}: invalid date {raw_date!r}: {e}") from e

            symbol = raw_sym.strip().upper()

            try:
                close = float(raw_close.strip().replace(",", ""))
            except ValueError as e:
                raise MalformedPriceDataError(f"row {row_idx}: invalid close price {raw_close!r}") from e

            if close < 0.0:
                raise NegativePriceError(f"row {row_idx}: close price cannot be negative: {close}")
            if close == 0.0:
                raise MalformedPriceDataError(f"row {row_idx}: close price cannot be zero")

            open_val = _parse_opt_float(row.get(open_col), row_idx, "open") if open_col else None
            high_val = _parse_opt_float(row.get(high_col), row_idx, "high") if high_col else None
            low_val = _parse_opt_float(row.get(low_col), row_idx, "low") if low_col else None
            vol_val = _parse_opt_float(row.get(vol_col), row_idx, "volume") if vol_col else None
            factor_val = _parse_opt_float(row.get(factor_col), row_idx, "factor") if factor_col else None
            factor = factor_val if factor_val is not None else 1.0
            if factor <= 0.0:
                raise MalformedPriceDataError(f"row {row_idx}: corporate action factor must be positive: {factor}")

            dataset.trading_dates.add(date_str)

            # Check if this is a benchmark symbol
            norm_bench = normalize_benchmark_symbol(symbol)
            if norm_bench in BENCHMARK_SYMBOLS or "NIFTY" in symbol:
                bench_map = dataset.benchmarks.setdefault(norm_bench, {})
                if date_str in bench_map and abs(bench_map[date_str] - close) > 1e-6:
                    raise DuplicatePriceConflictError(
                        f"row {row_idx}: conflicting benchmark price for {norm_bench} on {date_str}: "
                        f"{bench_map[date_str]} vs {close}"
                    )
                bench_map[date_str] = close

            # Symbol map
            sym_map = dataset.records_by_symbol.setdefault(symbol, {})
            if date_str in sym_map:
                existing = sym_map[date_str]
                if abs(existing.close - close) > 1e-6:
                    raise DuplicatePriceConflictError(
                        f"row {row_idx}: conflicting price for {symbol} on {date_str}: "
                        f"{existing.close} vs {close}"
                    )
            rec = DailyPriceRecord(
                date=date_str,
                symbol=symbol,
                open=open_val,
                high=high_val,
                low=low_val,
                close=close,
                volume=vol_val,
                corporate_action_factor=factor,
            )
            sym_map[date_str] = rec

        return dataset


def _load_json(path: Path, content_hash: str, source_type: str) -> PriceDataset:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise MalformedPriceDataError("JSON price feed root must be an object")

    dataset = PriceDataset(
        source_path=str(path),
        source_type=source_type,
        content_hash=content_hash,
    )

    prices_list = data.get("prices", [])
    if not isinstance(prices_list, list):
        raise MalformedPriceDataError("'prices' key must be a list")

    for idx, item in enumerate(prices_list):
        if not isinstance(item, dict):
            raise MalformedPriceDataError(f"item {idx}: record must be a dict")
        raw_date = item.get("date")
        raw_sym = item.get("symbol")
        raw_close = item.get("close")

        if not raw_date or not raw_sym or raw_close is None:
            raise MalformedPriceDataError(f"item {idx}: missing date, symbol, or close")

        try:
            dt = parse_iso_date(str(raw_date).strip())
            date_str = format_iso_date(dt)
        except Exception as e:
            raise MalformedPriceDataError(f"item {idx}: invalid date {raw_date!r}: {e}") from e

        symbol = str(raw_sym).strip().upper()
        try:
            close = float(raw_close)
        except (ValueError, TypeError) as e:
            raise MalformedPriceDataError(f"item {idx}: invalid close {raw_close!r}") from e

        if close < 0.0:
            raise NegativePriceError(f"item {idx}: close price cannot be negative: {close}")
        if close == 0.0:
            raise MalformedPriceDataError(f"item {idx}: close price cannot be zero")

        open_val = _opt_float_or_error(item.get("open"), idx, "open")
        high_val = _opt_float_or_error(item.get("high"), idx, "high")
        low_val = _opt_float_or_error(item.get("low"), idx, "low")
        vol_val = _opt_float_or_error(item.get("volume"), idx, "volume")
        factor = float(item.get("corporate_action_factor", 1.0))
        if factor <= 0.0:
            raise MalformedPriceDataError(f"item {idx}: corporate action factor must be positive: {factor}")

        dataset.trading_dates.add(date_str)

        norm_bench = normalize_benchmark_symbol(symbol)
        if norm_bench in BENCHMARK_SYMBOLS or "NIFTY" in symbol:
            bench_map = dataset.benchmarks.setdefault(norm_bench, {})
            if date_str in bench_map and abs(bench_map[date_str] - close) > 1e-6:
                raise DuplicatePriceConflictError(
                    f"item {idx}: conflicting benchmark price for {norm_bench} on {date_str}"
                )
            bench_map[date_str] = close

        sym_map = dataset.records_by_symbol.setdefault(symbol, {})
        if date_str in sym_map and abs(sym_map[date_str].close - close) > 1e-6:
            raise DuplicatePriceConflictError(
                f"item {idx}: conflicting price for {symbol} on {date_str}"
            )

        sym_map[date_str] = DailyPriceRecord(
            date=date_str,
            symbol=symbol,
            open=open_val,
            high=high_val,
            low=low_val,
            close=close,
            volume=vol_val,
            corporate_action_factor=factor,
        )

    # Optional explicit benchmark_prices block
    bench_list = data.get("benchmark_prices", [])
    if isinstance(bench_list, list):
        for idx, item in enumerate(bench_list):
            if not isinstance(item, dict):
                continue
            b_sym = normalize_benchmark_symbol(str(item.get("symbol", "NIFTY_50_TRI")))
            raw_d = item.get("date")
            raw_c = item.get("close")
            if not raw_d or raw_c is None:
                continue
            d_str = format_iso_date(parse_iso_date(str(raw_d).strip()))
            c_val = float(raw_c)
            if c_val <= 0.0:
                raise MalformedPriceDataError(f"benchmark close must be positive: {c_val}")
            dataset.benchmarks.setdefault(b_sym, {})[d_str] = c_val
            dataset.trading_dates.add(d_str)

    return dataset


def _parse_opt_float(val: Any, row_idx: int, field_name: str) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip().replace(",", "")
    if s == "" or s.lower() == "null" or s == "-":
        return None
    try:
        f = float(s)
        if f < 0.0:
            raise NegativePriceError(f"row {row_idx}: {field_name} cannot be negative: {f}")
        return f
    except ValueError as e:
        raise MalformedPriceDataError(f"row {row_idx}: invalid numeric for {field_name}: {val!r}") from e


def _opt_float_or_error(val: Any, idx: int, field_name: str) -> Optional[float]:
    if val is None:
        return None
    try:
        f = float(val)
        if f < 0.0:
            raise NegativePriceError(f"item {idx}: {field_name} cannot be negative: {f}")
        return f
    except (ValueError, TypeError) as e:
        raise MalformedPriceDataError(f"item {idx}: invalid numeric for {field_name}: {val!r}") from e
