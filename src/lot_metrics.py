#!/usr/bin/env python3
"""Aggregate lot/inspection time-series readings and flag outliers."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass
class Reading:
    timestamp: datetime
    lot_id: str
    metric: str
    value: float


@dataclass
class Aggregate:
    lot_id: str
    metric: str
    count: int
    minimum: float
    maximum: float
    mean: float
    stdev: float
    outliers: list[dict]


def parse_ts(raw: str) -> datetime:
    text = raw.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"bad timestamp: {raw!r}") from exc


def load_csv(path: Path) -> list[Reading]:
    rows: list[Reading] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"timestamp", "lot_id", "metric", "value"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise SystemExit(f"CSV must include columns: {', '.join(sorted(required))}")
        for i, row in enumerate(reader, start=2):
            try:
                rows.append(
                    Reading(
                        timestamp=parse_ts(row["timestamp"]),
                        lot_id=row["lot_id"].strip(),
                        metric=row["metric"].strip(),
                        value=float(row["value"]),
                    )
                )
            except (KeyError, ValueError) as exc:
                raise SystemExit(f"line {i}: {exc}") from exc
    if not rows:
        raise SystemExit("no readings found")
    return rows


def stdev(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(var)


def median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def modified_z(values: list[float]) -> list[float]:
    """Robust z-scores via median absolute deviation (MAD)."""
    if len(values) < 2:
        return [0.0] * len(values)
    med = median(values)
    deviations = [abs(v - med) for v in values]
    mad = median(deviations)
    if mad == 0:
        mean = sum(values) / len(values)
        sd = stdev(values, mean)
        if sd == 0:
            return [0.0] * len(values)
        return [abs(v - mean) / sd for v in values]
    return [0.6745 * abs(v - med) / mad for v in values]


def aggregate(readings: Iterable[Reading], sigma: float) -> list[Aggregate]:
    buckets: dict[tuple[str, str], list[Reading]] = defaultdict(list)
    for r in readings:
        buckets[(r.lot_id, r.metric)].append(r)

    out: list[Aggregate] = []
    for (lot_id, metric), items in sorted(buckets.items()):
        values = [r.value for r in items]
        mean = sum(values) / len(values)
        sd = stdev(values, mean)
        scores = modified_z(values)
        outliers: list[dict] = []
        for r, z in zip(items, scores):
            if z > sigma:
                outliers.append(
                    {
                        "timestamp": r.timestamp.isoformat(),
                        "value": r.value,
                        "z": round(z, 3),
                    }
                )
        out.append(
            Aggregate(
                lot_id=lot_id,
                metric=metric,
                count=len(values),
                minimum=min(values),
                maximum=max(values),
                mean=round(mean, 4),
                stdev=round(sd, 4),
                outliers=outliers,
            )
        )
    return out


def print_table(aggs: list[Aggregate]) -> None:
    headers = ("lot_id", "metric", "n", "min", "max", "mean", "stdev", "outliers")
    rows = [
        (
            a.lot_id,
            a.metric,
            str(a.count),
            f"{a.minimum:.3f}",
            f"{a.maximum:.3f}",
            f"{a.mean:.3f}",
            f"{a.stdev:.3f}",
            str(len(a.outliers)),
        )
        for a in aggs
    ]
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for r in rows:
        print(fmt.format(*r))
    flagged = sum(len(a.outliers) for a in aggs)
    print(f"\nseries={len(aggs)}  outlier_points={flagged}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Lot inspection time-series aggregator")
    p.add_argument("--file", "-f", type=Path, required=True, help="CSV readings file")
    p.add_argument("--sigma", type=float, default=3.5, help="modified z-score threshold (default 3.5)")
    p.add_argument("--json", type=Path, help="optional JSON output path")
    args = p.parse_args(argv)

    if args.sigma <= 0:
        raise SystemExit("--sigma must be > 0")
    if not args.file.is_file():
        raise SystemExit(f"file not found: {args.file}")

    readings = load_csv(args.file)
    aggs = aggregate(readings, args.sigma)
    print_table(aggs)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "sigma": args.sigma,
            "source": str(args.file),
            "series": [asdict(a) for a in aggs],
        }
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
