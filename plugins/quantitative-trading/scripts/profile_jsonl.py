#!/usr/bin/env python3
"""Profile JSONL telemetry without printing sensitive raw payloads."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import re
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, IO


REDACTED_KEY_PARTS = (
    "secret",
    "token",
    "key",
    "wallet",
    "address",
    "signature",
    "auth",
    "bearer",
)
SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9_.:_-]{1,64}$")
HEX_ID_RE = re.compile(r"^(0x)?[0-9a-fA-F]{16,}$")
LONG_NUMERIC_ID_RE = re.compile(r"^[0-9]{12,}$")
MAX_NUMERIC_METRIC_ABS = 1_000_000_000_000
TS_KEY_CANDIDATES = ("ts", "timestamp", "time", "created_at", "at", "t")


def parse_when(raw: str) -> float:
    """Parse ISO-8601 or Unix epoch seconds/milliseconds."""
    try:
        return epoch_from_number(float(raw))
    except ValueError:
        pass
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--limit", type=int, default=20_000)
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--since", type=parse_when)
    parser.add_argument("--until", type=parse_when)
    parser.add_argument("--group-by")
    parser.add_argument("--metric", action="append", default=[])
    return parser.parse_args()


def epoch_from_number(value: float) -> float:
    if value > 1e11:
        return value / 1000.0
    if value > 1e8:
        return value
    raise ValueError(f"not a plausible epoch: {value}")


def row_timestamp(flat: dict[str, Any]) -> float | None:
    for key in TS_KEY_CANDIDATES:
        value = flat.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                return epoch_from_number(float(value))
            except ValueError:
                continue
        if isinstance(value, str):
            try:
                return parse_when(value)
            except ValueError:
                continue
    return None


def iso_utc(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in REDACTED_KEY_PARTS)


def safe_label(value: Any) -> str:
    if value is None:
        return "unknown"
    label = str(value).strip()
    if not label or SAFE_LABEL_RE.fullmatch(label) is None:
        return "redacted_label"
    if any(part in label.lower() for part in REDACTED_KEY_PARTS):
        return "redacted_label"
    if HEX_ID_RE.fullmatch(label) or LONG_NUMERIC_ID_RE.fullmatch(label):
        return "redacted_label"
    return label


def safe_path_segment(value: Any) -> str:
    segment = str(value).strip()
    if not segment:
        return "empty_key"
    if any(part in segment.lower() for part in REDACTED_KEY_PARTS):
        return "redacted_key"
    if HEX_ID_RE.fullmatch(segment) or LONG_NUMERIC_ID_RE.fullmatch(segment):
        return "dynamic_id"
    if SAFE_LABEL_RE.fullmatch(segment) is None:
        return "dynamic_key"
    return segment


def numeric_metric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and abs(value) <= MAX_NUMERIC_METRIC_ABS:
        return float(value)
    if isinstance(value, float) and math.isfinite(value):
        return value
    return None


def flatten(prefix: str, value: Any, out: dict[str, Any]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            segment = safe_path_segment(key)
            next_prefix = f"{prefix}.{segment}" if prefix else segment
            flatten(next_prefix, item, out)
    elif isinstance(value, (str, int, float, bool)) or value is None:
        out[prefix] = value


def open_text(path: Path) -> IO[str]:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open(encoding="utf-8", errors="replace")


def iter_tail_lines(path: Path, limit: int) -> list[str]:
    if limit < 1:
        raise ValueError("--limit must be at least 1")
    with open_text(path) as handle:
        return list(deque(handle, maxlen=limit))


def percentile(values: list[float], fraction: float) -> float:
    if len(values) == 1:
        return values[0]
    rank = fraction * (len(values) - 1)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return values[low]
    weight = rank - low
    return values[low] * (1 - weight) + values[high] * weight


def summary(values: list[float]) -> str:
    ordered = sorted(values)
    deviation = pstdev(ordered) if len(ordered) > 1 else 0.0
    return (
        f"n={len(ordered)} min={ordered[0]:.6g} "
        f"p05={percentile(ordered, 0.05):.6g} "
        f"median={percentile(ordered, 0.5):.6g} "
        f"mean={mean(ordered):.6g} "
        f"p95={percentile(ordered, 0.95):.6g} "
        f"max={ordered[-1]:.6g} sd={deviation:.6g}"
    )


def main() -> None:
    args = parse_args()
    if not args.path.is_file():
        raise SystemExit(f"JSONL file not found: {args.path}")
    if args.top < 1:
        raise SystemExit("--top must be at least 1")
    if args.since is not None and args.until is not None and args.since > args.until:
        raise SystemExit("--since must not be after --until")

    event_counts: Counter[str] = Counter()
    field_counts: Counter[str] = Counter()
    numeric_values: dict[str, list[float]] = defaultdict(list)
    group_rows: Counter[str] = Counter()
    group_metrics: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    parsed_rows = malformed_rows = rows_no_ts_skipped = rows_outside_window = 0
    ts_min: float | None = None
    ts_max: float | None = None
    time_filtered = args.since is not None or args.until is not None

    try:
        lines = iter_tail_lines(args.path, args.limit)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            malformed_rows += 1
            continue
        if not isinstance(row, dict):
            malformed_rows += 1
            continue

        flat: dict[str, Any] = {}
        flatten("", row, flat)
        row_ts = row_timestamp(flat)
        if time_filtered and row_ts is None:
            rows_no_ts_skipped += 1
            continue
        if row_ts is not None:
            if args.since is not None and row_ts < args.since:
                rows_outside_window += 1
                continue
            if args.until is not None and row_ts > args.until:
                rows_outside_window += 1
                continue

        parsed_rows += 1
        if row_ts is not None:
            ts_min = row_ts if ts_min is None else min(ts_min, row_ts)
            ts_max = row_ts if ts_max is None else max(ts_max, row_ts)
        event = safe_label(row.get("event") or row.get("type") or row.get("status"))
        event_counts[event] += 1

        group_label: str | None = None
        if args.group_by:
            group_label = safe_label(flat.get(args.group_by))
            group_rows[group_label] += 1

        for key, value in flat.items():
            if is_sensitive_key(key):
                continue
            field_counts[key] += 1
            number = numeric_metric(value)
            if number is None:
                continue
            numeric_values[key].append(number)
            if group_label is not None and key in args.metric:
                group_metrics[group_label][key].append(number)

    print(f"path: {args.path}")
    print(f"rows_parsed: {parsed_rows}")
    print(f"rows_malformed: {malformed_rows}")
    if time_filtered:
        print(f"rows_outside_window: {rows_outside_window}")
        print(f"rows_no_ts_skipped: {rows_no_ts_skipped}")
    if ts_min is not None and ts_max is not None:
        print(f"covered_window_utc: {iso_utc(ts_min)} .. {iso_utc(ts_max)}")
    else:
        print("covered_window_utc: unknown (no parseable timestamps)")

    print("\ntop_events:")
    for label, count in event_counts.most_common(args.top):
        print(f"  {label}: {count}")
    print("\ntop_fields:")
    for field, count in field_counts.most_common(args.top):
        print(f"  {field}: {count}")
    print("\nnumeric_fields:")
    ranked = sorted(numeric_values.items(), key=lambda item: len(item[1]), reverse=True)
    for field, values in ranked[: args.top]:
        print(f"  {field}: {summary(values)}")

    if args.group_by:
        print(f"\ngroups_by[{args.group_by}]:")
        for label, count in group_rows.most_common(args.top):
            print(f"  {label}: rows={count}")
            for metric in args.metric:
                values = group_metrics[label].get(metric, [])
                if values:
                    print(f"    {metric}: {summary(values)}")


if __name__ == "__main__":
    main()
